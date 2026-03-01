"""
PrimeHaul OS — Email Automation Engine.

Event-driven email sequences with queued sending, bounce/unsubscribe
handling, and GDPR compliance.  Runs as APScheduler background jobs.
"""

import hashlib
import hmac
import logging
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    Company,
    EmailBounce,
    EmailEnrollment,
    EmailPreference,
    EmailQueue,
    EmailSequence,
    EmailSequenceStep,
    EmailTemplate,
)

logger = logging.getLogger("primehaul.email_engine")


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_template(body: str, context: dict) -> str:
    """Replace {{var}} placeholders. Missing keys become empty string."""
    def _replace(match):
        key = match.group(1).strip()
        return str(context.get(key, ""))
    return re.sub(r"\{\{(\s*\w+\s*)\}\}", _replace, body)


# ---------------------------------------------------------------------------
# Suppression checks
# ---------------------------------------------------------------------------

def is_suppressed(email: str, category: str, db: Session) -> bool:
    """Return True if the email should NOT receive this category."""
    bounce = db.query(EmailBounce).filter(EmailBounce.email == email).first()
    if bounce and bounce.suppressed:
        return True

    pref = db.query(EmailPreference).filter(EmailPreference.email == email).first()
    if pref:
        if pref.unsubscribed_all:
            return True
        if pref.unsubscribed_categories and category in pref.unsubscribed_categories:
            return True

    return False


# ---------------------------------------------------------------------------
# Unsubscribe URL generation (HMAC-signed)
# ---------------------------------------------------------------------------

def generate_unsubscribe_url(email: str, category: str) -> str:
    """Generate an HMAC-SHA256 signed unsubscribe URL."""
    payload = f"{email}|{category}"
    sig = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    params = urllib.parse.urlencode({"email": email, "category": category, "sig": sig})
    return f"/email/unsubscribe?{params}"


def verify_unsubscribe_signature(email: str, category: str, sig: str) -> bool:
    """Verify an unsubscribe HMAC signature."""
    payload = f"{email}|{category}"
    expected = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(sig, expected)


# ---------------------------------------------------------------------------
# Enrollment management
# ---------------------------------------------------------------------------

def enroll_in_sequence(
    trigger_event: str,
    to_email: str,
    context: dict,
    company_id,
    job_id=None,
    db: Session | None = None,
):
    """Enroll an email in the matching active sequence (if any)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        seq = db.query(EmailSequence).filter(
            EmailSequence.trigger_event == trigger_event,
            EmailSequence.is_active.is_(True),
        ).first()
        if not seq or not seq.steps:
            return

        # Check for duplicate active enrollment
        existing = db.query(EmailEnrollment).filter(
            EmailEnrollment.to_email == to_email,
            EmailEnrollment.sequence_id == seq.id,
            EmailEnrollment.status == "active",
        ).first()
        if existing:
            logger.info("[EMAIL-ENGINE] %s already enrolled in %s", to_email, seq.slug)
            return

        # Check suppression
        category = seq.steps[0].template.email_category if seq.steps else "follow_up"
        if is_suppressed(to_email, category, db):
            logger.info("[EMAIL-ENGINE] %s suppressed, skipping enrollment", to_email)
            return

        first_step = seq.steps[0]
        next_send = datetime.now(timezone.utc) + timedelta(minutes=first_step.delay_minutes)

        enrollment = EmailEnrollment(
            sequence_id=seq.id,
            to_email=to_email,
            company_id=company_id,
            job_id=job_id,
            context_json=context,
            current_step=0,
            status="active",
            next_send_at=next_send,
        )
        db.add(enrollment)
        db.commit()
        logger.info("[EMAIL-ENGINE] Enrolled %s in sequence '%s'", to_email, seq.slug)
    except Exception:
        logger.exception("[EMAIL-ENGINE] Failed to enroll %s", to_email)
        if own_session:
            db.rollback()
    finally:
        if own_session:
            db.close()


def cancel_enrollment(to_email: str, trigger_event: str, db: Session | None = None):
    """Cancel active enrollments for a specific trigger."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        enrollments = (
            db.query(EmailEnrollment)
            .join(EmailSequence)
            .filter(
                EmailEnrollment.to_email == to_email,
                EmailEnrollment.status == "active",
                EmailSequence.trigger_event == trigger_event,
            )
            .all()
        )
        for e in enrollments:
            e.status = "cancelled"
        if enrollments:
            db.commit()
            logger.info("[EMAIL-ENGINE] Cancelled %d enrollment(s) for %s/%s", len(enrollments), to_email, trigger_event)
    except Exception:
        logger.exception("[EMAIL-ENGINE] Failed to cancel enrollment")
        if own_session:
            db.rollback()
    finally:
        if own_session:
            db.close()


def cancel_all_enrollments(email: str, db: Session):
    """Cancel ALL active enrollments for an email (used by unsubscribe)."""
    enrollments = db.query(EmailEnrollment).filter(
        EmailEnrollment.to_email == email,
        EmailEnrollment.status == "active",
    ).all()
    for e in enrollments:
        e.status = "cancelled"
    if enrollments:
        db.commit()
        logger.info("[EMAIL-ENGINE] Cancelled all %d enrollment(s) for %s", len(enrollments), email)


# ---------------------------------------------------------------------------
# APScheduler job: process enrollments → create queue entries
# ---------------------------------------------------------------------------

def process_enrollments():
    """Advance active enrollments whose next_send_at has passed."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        enrollments = (
            db.query(EmailEnrollment)
            .filter(
                EmailEnrollment.status == "active",
                EmailEnrollment.next_send_at <= now,
            )
            .limit(100)
            .all()
        )

        for enrollment in enrollments:
            try:
                seq = enrollment.sequence
                steps = sorted(seq.steps, key=lambda s: s.step_order)

                if enrollment.current_step >= len(steps):
                    enrollment.status = "completed"
                    db.commit()
                    continue

                step = steps[enrollment.current_step]
                tmpl = step.template

                # Check suppression
                if is_suppressed(enrollment.to_email, tmpl.email_category, db):
                    enrollment.status = "cancelled"
                    db.commit()
                    logger.info("[EMAIL-ENGINE] Suppressed mid-sequence: %s", enrollment.to_email)
                    continue

                # Render subject and body
                ctx = enrollment.context_json or {}
                rendered_subject = render_template(tmpl.subject, ctx)
                rendered_body = render_template(tmpl.body_html, ctx)

                # Create queue entry
                queue_item = EmailQueue(
                    to_email=enrollment.to_email,
                    subject=rendered_subject,
                    body_html=rendered_body,
                    email_type=f"sequence_{seq.slug}",
                    email_category=tmpl.email_category,
                    company_id=enrollment.company_id,
                    job_id=enrollment.job_id,
                    enrollment_id=enrollment.id,
                    status="pending",
                    send_at=now,
                )
                db.add(queue_item)

                # Advance to next step
                enrollment.current_step += 1
                if enrollment.current_step >= len(steps):
                    enrollment.status = "completed"
                    enrollment.next_send_at = None
                else:
                    next_step = steps[enrollment.current_step]
                    enrollment.next_send_at = now + timedelta(minutes=next_step.delay_minutes)

                db.commit()
            except Exception:
                db.rollback()
                logger.exception("[EMAIL-ENGINE] Error processing enrollment %s", enrollment.id)

    except Exception:
        logger.exception("[EMAIL-ENGINE] process_enrollments failed")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# APScheduler job: send queued emails
# ---------------------------------------------------------------------------

def process_email_queue():
    """Send pending emails from the queue."""
    from app.notifications import send_email, _record_bounce

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        items = (
            db.query(EmailQueue)
            .filter(
                EmailQueue.status == "pending",
                EmailQueue.send_at <= now,
            )
            .order_by(EmailQueue.send_at)
            .limit(50)
            .all()
        )

        for item in items:
            try:
                # Final suppression check
                if is_suppressed(item.to_email, item.email_category, db):
                    item.status = "suppressed"
                    db.commit()
                    continue

                # Append unsubscribe footer for non-transactional emails
                body_html = item.body_html
                if item.email_category != "transactional":
                    unsub_url = generate_unsubscribe_url(item.to_email, item.email_category)
                    footer = (
                        '<div style="margin-top:32px;padding-top:16px;border-top:1px solid #333;'
                        'text-align:center;font-size:12px;color:#888;">'
                        f'<a href="{unsub_url}" style="color:#888;text-decoration:underline;">'
                        'Unsubscribe</a> from these emails'
                        '</div>'
                    )
                    body_html += footer

                # Load company SMTP config if available
                smtp_config = None
                if item.company_id:
                    company = db.query(Company).filter(Company.id == item.company_id).first()
                    if company and company.smtp_host and company.smtp_username and company.smtp_password:
                        smtp_config = {
                            "host": company.smtp_host,
                            "port": company.smtp_port or 587,
                            "username": company.smtp_username,
                            "password": company.smtp_password,
                            "from_email": company.smtp_from_email or company.smtp_username,
                        }

                success = send_email(
                    to_email=item.to_email,
                    subject=item.subject,
                    html_body=body_html,
                    smtp_config=smtp_config,
                    email_type=item.email_type,
                    company_id=item.company_id,
                    job_id=item.job_id,
                    skip_log=False,
                )

                if success:
                    item.status = "sent"
                    item.attempts += 1
                else:
                    item.attempts += 1
                    backoff = min(2 ** item.attempts, 60)
                    if item.attempts >= item.max_attempts:
                        item.status = "failed"
                        item.last_error = "Max attempts reached"
                    else:
                        item.send_at = now + timedelta(minutes=backoff)
                        item.last_error = "Send failed, retrying"

                db.commit()
            except Exception as exc:
                db.rollback()
                item.attempts += 1
                item.last_error = str(exc)[:500]
                if item.attempts >= item.max_attempts:
                    item.status = "failed"
                db.commit()
                logger.exception("[EMAIL-ENGINE] Queue send error for %s", item.id)

    except Exception:
        logger.exception("[EMAIL-ENGINE] process_email_queue failed")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Seed default sequences and templates (idempotent)
# ---------------------------------------------------------------------------

def seed_default_sequences():
    """Create default sequences and templates if they don't already exist."""
    db = SessionLocal()
    try:
        # Check if already seeded
        existing = db.query(EmailSequence).count()
        if existing > 0:
            logger.info("[EMAIL-ENGINE] Sequences already exist (%d), skipping seed", existing)
            return

        sequences = [
            {
                "slug": "quote-follow-up",
                "name": "Quote Follow-Up",
                "trigger_event": "quote_approved",
                "steps": [
                    {"delay": 120, "slug": "quote-fu-1", "name": "Quote Follow-Up Step 1",
                     "subject": "Your quote from {{company_name}} — any questions?",
                     "category": "follow_up"},
                    {"delay": 1440, "slug": "quote-fu-2", "name": "Quote Follow-Up Step 2",
                     "subject": "{{customer_name}}, your moving quote is waiting",
                     "category": "follow_up"},
                    {"delay": 4320, "slug": "quote-fu-3", "name": "Quote Follow-Up Step 3",
                     "subject": "Last chance to book your move with {{company_name}}",
                     "category": "follow_up"},
                ],
            },
            {
                "slug": "onboarding-drip",
                "name": "Onboarding Drip",
                "trigger_event": "company_onboarded",
                "steps": [
                    {"delay": 1440, "slug": "onboard-1", "name": "Onboarding Step 1",
                     "subject": "Quick tip: Send your first AI survey in 2 minutes",
                     "category": "marketing"},
                    {"delay": 4320, "slug": "onboard-2", "name": "Onboarding Step 2",
                     "subject": "How {{company_name}} can save 5 hours/week on quoting",
                     "category": "marketing"},
                    {"delay": 10080, "slug": "onboard-3", "name": "Onboarding Step 3",
                     "subject": "Your first week with PrimeHaul — how's it going?",
                     "category": "marketing"},
                    {"delay": 20160, "slug": "onboard-4", "name": "Onboarding Step 4",
                     "subject": "Unlock the marketplace: Get leads sent directly to you",
                     "category": "marketing"},
                    {"delay": 30240, "slug": "onboard-5", "name": "Onboarding Step 5",
                     "subject": "Your trial ends in 9 days — here's what you'll lose",
                     "category": "marketing"},
                ],
            },
            {
                "slug": "survey-nudge",
                "name": "Survey Nudge",
                "trigger_event": "survey_invitation_sent",
                "steps": [
                    {"delay": 1440, "slug": "survey-nudge-1", "name": "Survey Nudge Step 1",
                     "subject": "Reminder: Complete your moving survey for {{company_name}}",
                     "category": "follow_up"},
                    {"delay": 4320, "slug": "survey-nudge-2", "name": "Survey Nudge Step 2",
                     "subject": "{{customer_name}}, your free moving estimate is almost ready",
                     "category": "follow_up"},
                ],
            },
            {
                "slug": "post-move-review",
                "name": "Post-Move Review",
                "trigger_event": "job_completed",
                "steps": [
                    {"delay": 1440, "slug": "review-1", "name": "Post-Move Review Step 1",
                     "subject": "How was your move with {{company_name}}?",
                     "category": "follow_up"},
                    {"delay": 10080, "slug": "review-2", "name": "Post-Move Review Step 2",
                     "subject": "{{customer_name}}, your feedback helps other movers",
                     "category": "follow_up"},
                ],
            },
        ]

        for seq_data in sequences:
            seq = EmailSequence(
                slug=seq_data["slug"],
                name=seq_data["name"],
                trigger_event=seq_data["trigger_event"],
                is_active=True,
            )
            db.add(seq)
            db.flush()

            for i, step_data in enumerate(seq_data["steps"]):
                tmpl = EmailTemplate(
                    slug=step_data["slug"],
                    name=step_data["name"],
                    subject=step_data["subject"],
                    body_html=_default_body(step_data["subject"]),
                    email_category=step_data["category"],
                    is_active=True,
                )
                db.add(tmpl)
                db.flush()

                step = EmailSequenceStep(
                    sequence_id=seq.id,
                    template_id=tmpl.id,
                    step_order=i,
                    delay_minutes=step_data["delay"],
                )
                db.add(step)

        db.commit()
        logger.info("[EMAIL-ENGINE] Default sequences seeded (4 sequences, 12 templates)")
    except Exception:
        db.rollback()
        logger.exception("[EMAIL-ENGINE] Failed to seed default sequences")
    finally:
        db.close()


def _default_body(subject: str) -> str:
    """Generate a simple default email body from the subject line."""
    return (
        '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;">'
        f'<h2 style="color:#1a1a2e;margin-bottom:16px;">{subject}</h2>'
        '<p style="color:#555;line-height:1.6;">{{body_text}}</p>'
        '<p style="margin-top:24px;">'
        '<a href="{{action_url}}" style="display:inline-block;padding:12px 24px;'
        'background:#2ee59d;color:#000;text-decoration:none;border-radius:6px;font-weight:700;">'
        'Take Action</a></p>'
        '<p style="color:#999;font-size:13px;margin-top:32px;">'
        '{{company_name}}<br>{{company_phone}}<br>{{company_email}}</p>'
        '</div>'
    )
