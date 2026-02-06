"""
PrimeHaul Sales Outreach Automation

Private dashboard for:
- Auto-scraping removal company leads
- Sending cold email sequences
- Reading and auto-replying to responses
- Tracking pipeline
"""

import os
import re
import json
import imaplib
import email
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.database import get_db
from app.models import Base
import logging

logger = logging.getLogger(__name__)


# ============================================
# DATABASE MODELS
# ============================================

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    REPLIED = "replied"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    SIGNED_UP = "signed_up"
    DEAD = "dead"


class Lead(Base):
    __tablename__ = "outreach_leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50))
    website = Column(String(255))
    location = Column(String(100))
    source = Column(String(50))  # Manual, Checkatrade, Yell, etc.

    status = Column(String(20), default="new")
    emails_sent = Column(Integer, default=0)
    last_contacted = Column(DateTime)
    last_reply = Column(DateTime)
    next_followup = Column(DateTime)

    notes = Column(Text)
    reply_summary = Column(Text)  # AI summary of their reply
    sentiment = Column(String(20))  # positive, negative, neutral, question

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OutreachEmail(Base):
    __tablename__ = "outreach_emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    direction = Column(String(10))  # sent, received
    subject = Column(String(255))
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    message_id = Column(String(255))  # For threading


# ============================================
# EMAIL TEMPLATES
# ============================================

EMAIL_TEMPLATES = {
    "initial": {
        "subject": "Quick question about your quoting process",
        "body": """Hi {first_name},

Spotted {company_name} online - looks like you've built a solid reputation.

Quick question: how long does it take you to quote a 3-bed house move right now?

We've built a tool that lets your customers photograph their rooms and get an AI-calculated quote in under 5 minutes. No site visits, no phone tag.

It's white-labelled to your brand. Customers think it's your tech.

3 free quotes to try it - no card needed: {demo_link}

Cheers,
Jay
PrimeHaul

P.S. Takes 2 minutes to set up. Most companies are quoting the same day."""
    },

    "followup_1": {
        "subject": "Re: Quick question about your quoting process",
        "body": """Hi {first_name},

Just bumping this - did you get a chance to look?

One of our removal companies quoted 14 jobs last week using the AI tool. Said it used to take 2 hours of phone calls to do the same.

Here's the link again: {demo_link}

Happy to jump on a quick call if easier.

Jay"""
    },

    "followup_2": {
        "subject": "Last one from me",
        "body": """Hi {first_name},

I'll assume timing's not right.

If you ever want to quote jobs 10x faster without hiring more staff, the link's here: {demo_link}

No hard feelings - good luck with the busy season.

Jay"""
    },

    "reply_interested": {
        "subject": "Re: {original_subject}",
        "body": """Hi {first_name},

Great to hear from you!

Here's your personalised demo link - takes about 2 minutes to set up: {demo_link}

Once you're in, you can:
1. Customise your pricing
2. Add your branding
3. Send your first quote link to a real customer

Any questions, just reply here or call me on 07XXX XXX XXX.

Jay"""
    },

    "reply_question": {
        "subject": "Re: {original_subject}",
        "body": """Hi {first_name},

Good question!

{answer}

Let me know if that helps, or happy to jump on a quick call to walk through it.

Jay"""
    },

    "reply_objection": {
        "subject": "Re: {original_subject}",
        "body": """Hi {first_name},

Totally understand.

{objection_response}

No pressure either way - the link's there if you change your mind: {demo_link}

All the best,
Jay"""
    }
}

# Common objection responses
OBJECTION_RESPONSES = {
    "too busy": "Most of our customers said the same thing - that's exactly why they needed it. The tool handles the quoting so you can focus on the actual moves.",
    "already have software": "Fair enough! Out of curiosity, does your current system let customers photograph rooms and get instant AI quotes? That's the bit most companies are missing.",
    "too expensive": "Actually, it's pay-per-quote (starts at £6.99/quote for bulk packs). No monthly fees. Most companies make it back on the first job they win.",
    "not interested": "No worries at all. I'll leave you be. If things change, the offer stands.",
    "how does it work": "Dead simple: You send customers a link → They photograph each room → AI counts everything and calculates the quote → You review and approve in 30 seconds. The whole thing takes under 5 minutes.",
    "is it accurate": "The AI has been trained on thousands of UK removals. It's typically within 5-10% of manual estimates, and you can always adjust before approving.",
}


# ============================================
# EMAIL FUNCTIONS
# ============================================

def get_smtp_config():
    """Get SMTP configuration from environment"""
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
        "from_email": os.environ.get("OUTREACH_EMAIL", os.environ.get("SMTP_USER", "")),
        "from_name": os.environ.get("OUTREACH_NAME", "Jay from PrimeHaul"),
    }


def get_imap_config():
    """Get IMAP configuration for reading replies"""
    return {
        "host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
        "port": int(os.environ.get("IMAP_PORT", 993)),
        "user": os.environ.get("SMTP_USER", ""),
        "password": os.environ.get("SMTP_PASSWORD", ""),
    }


def send_outreach_email(
    to_email: str,
    subject: str,
    body: str,
    reply_to_message_id: str = None
) -> tuple[bool, str]:
    """
    Send an outreach email

    Returns:
        (success, message_id or error)
    """
    config = get_smtp_config()

    if not config["user"] or not config["password"]:
        return False, "SMTP not configured"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config['from_name']} <{config['from_email']}>"
        msg['To'] = to_email

        # Generate message ID for threading
        message_id = f"<{uuid.uuid4()}@primehaul.co.uk>"
        msg['Message-ID'] = message_id

        if reply_to_message_id:
            msg['In-Reply-To'] = reply_to_message_id
            msg['References'] = reply_to_message_id

        # Plain text version
        msg.attach(MIMEText(body, 'plain'))

        # HTML version (simple formatting)
        html_body = body.replace('\n', '<br>')
        html = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333;">
        {html_body}
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Send
        with smtplib.SMTP(config["host"], config["port"]) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)

        return True, message_id

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False, str(e)


def check_for_replies(db: Session, since_hours: int = 24) -> List[Dict]:
    """
    Check inbox for replies to outreach emails

    Returns list of new replies with parsed info
    """
    config = get_imap_config()

    if not config["user"] or not config["password"]:
        return []

    replies = []

    try:
        # Connect to IMAP
        mail = imaplib.IMAP4_SSL(config["host"], config["port"])
        mail.login(config["user"], config["password"])
        mail.select('INBOX')

        # Search for recent emails
        since_date = (datetime.now() - timedelta(hours=since_hours)).strftime("%d-%b-%Y")
        _, message_nums = mail.search(None, f'(SINCE {since_date})')

        for num in message_nums[0].split():
            _, msg_data = mail.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            from_email = email.utils.parseaddr(msg['From'])[1]
            subject = msg['Subject'] or ""
            message_id = msg['Message-ID']
            in_reply_to = msg.get('In-Reply-To', '')

            # Check if this is a reply to one of our emails
            lead = db.query(Lead).filter(Lead.email == from_email).first()
            if not lead:
                continue

            # Check if we already processed this
            existing = db.query(OutreachEmail).filter(
                OutreachEmail.message_id == message_id
            ).first()
            if existing:
                continue

            # Extract body
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Analyze sentiment
            sentiment = analyze_reply_sentiment(body_text)

            replies.append({
                "lead_id": str(lead.id),
                "lead_name": lead.company_name,
                "from_email": from_email,
                "subject": subject,
                "body": body_text,
                "message_id": message_id,
                "sentiment": sentiment,
            })

            # Save the reply
            outreach_email = OutreachEmail(
                lead_id=lead.id,
                direction="received",
                subject=subject,
                body=body_text,
                message_id=message_id,
            )
            db.add(outreach_email)

            # Update lead
            lead.last_reply = datetime.utcnow()
            lead.status = "replied"
            lead.sentiment = sentiment

            db.commit()

        mail.close()
        mail.logout()

    except Exception as e:
        logger.error(f"Error checking replies: {e}")

    return replies


def analyze_reply_sentiment(body: str) -> str:
    """
    Simple sentiment analysis on reply

    Returns: positive, negative, neutral, question
    """
    body_lower = body.lower()

    # Positive signals
    positive_words = ['interested', 'sounds good', 'tell me more', 'yes', 'great', 'love', 'perfect', 'demo', 'try', 'sign up', 'how do i', 'send me']
    if any(word in body_lower for word in positive_words):
        return "positive"

    # Negative signals
    negative_words = ['not interested', 'no thanks', 'unsubscribe', 'stop', 'remove', 'don\'t contact', 'already have', 'not for us', 'too busy']
    if any(word in body_lower for word in negative_words):
        return "negative"

    # Question signals
    question_words = ['how', 'what', 'why', 'when', 'who', 'does it', 'can it', 'is it', '?']
    if any(word in body_lower for word in question_words):
        return "question"

    return "neutral"


def generate_auto_reply(lead: Lead, their_reply: str, sentiment: str) -> tuple[str, str]:
    """
    Generate an appropriate auto-reply based on sentiment

    Returns: (subject, body)
    """
    first_name = lead.company_name.split()[0] if lead.company_name else "there"
    demo_link = f"https://app.primehaul.co.uk/signup?ref={lead.email.split('@')[0]}"

    if sentiment == "positive":
        template = EMAIL_TEMPLATES["reply_interested"]
        subject = template["subject"].replace("{original_subject}", "Quick question about your quoting process")
        body = template["body"].format(
            first_name=first_name,
            demo_link=demo_link
        )

    elif sentiment == "negative":
        # Check for specific objection
        their_reply_lower = their_reply.lower()
        objection_response = OBJECTION_RESPONSES.get("not interested")

        for key, response in OBJECTION_RESPONSES.items():
            if key in their_reply_lower:
                objection_response = response
                break

        template = EMAIL_TEMPLATES["reply_objection"]
        subject = template["subject"].replace("{original_subject}", "Quick question about your quoting process")
        body = template["body"].format(
            first_name=first_name,
            objection_response=objection_response,
            demo_link=demo_link
        )

    elif sentiment == "question":
        # Try to match their question to an answer
        their_reply_lower = their_reply.lower()
        answer = "Happy to explain more - what specifically would you like to know?"

        if "how does it work" in their_reply_lower or "how it works" in their_reply_lower:
            answer = OBJECTION_RESPONSES["how does it work"]
        elif "accurate" in their_reply_lower or "reliable" in their_reply_lower:
            answer = OBJECTION_RESPONSES["is it accurate"]
        elif "cost" in their_reply_lower or "price" in their_reply_lower or "expensive" in their_reply_lower:
            answer = OBJECTION_RESPONSES["too expensive"]

        template = EMAIL_TEMPLATES["reply_question"]
        subject = template["subject"].replace("{original_subject}", "Quick question about your quoting process")
        body = template["body"].format(
            first_name=first_name,
            answer=answer
        )

    else:  # neutral
        template = EMAIL_TEMPLATES["reply_interested"]
        subject = template["subject"].replace("{original_subject}", "Quick question about your quoting process")
        body = template["body"].format(
            first_name=first_name,
            demo_link=demo_link
        )

    return subject, body


# ============================================
# AUTOMATION FUNCTIONS
# ============================================

def get_leads_to_contact(db: Session, limit: int = 10) -> List[Lead]:
    """Get leads that need to be contacted"""
    # New leads that haven't been contacted
    new_leads = db.query(Lead).filter(
        Lead.status == "new",
        Lead.email.isnot(None),
        Lead.email != ""
    ).limit(limit).all()

    return new_leads


def get_leads_for_followup(db: Session, limit: int = 10) -> List[Lead]:
    """Get leads that need a follow-up"""
    now = datetime.utcnow()

    # Leads contacted but no reply, and enough time has passed
    followup_leads = db.query(Lead).filter(
        Lead.status == "contacted",
        Lead.emails_sent < 3,  # Max 3 emails
        Lead.next_followup <= now
    ).limit(limit).all()

    return followup_leads


def send_initial_email(lead: Lead, db: Session) -> bool:
    """Send initial cold email to a lead"""
    template = EMAIL_TEMPLATES["initial"]

    first_name = lead.company_name.split()[0] if lead.company_name else "there"
    demo_link = f"https://app.primehaul.co.uk/signup?ref={lead.email.split('@')[0]}"

    subject = template["subject"]
    body = template["body"].format(
        first_name=first_name,
        company_name=lead.company_name,
        demo_link=demo_link
    )

    success, message_id = send_outreach_email(lead.email, subject, body)

    if success:
        # Save sent email
        outreach_email = OutreachEmail(
            lead_id=lead.id,
            direction="sent",
            subject=subject,
            body=body,
            message_id=message_id,
        )
        db.add(outreach_email)

        # Update lead
        lead.status = "contacted"
        lead.emails_sent = 1
        lead.last_contacted = datetime.utcnow()
        lead.next_followup = datetime.utcnow() + timedelta(days=3)

        db.commit()
        return True

    return False


def send_followup_email(lead: Lead, db: Session) -> bool:
    """Send follow-up email based on how many we've sent"""
    emails_sent = lead.emails_sent or 0

    if emails_sent >= 3:
        lead.status = "dead"
        db.commit()
        return False

    template_key = f"followup_{emails_sent}"
    if template_key not in EMAIL_TEMPLATES:
        template_key = "followup_2"  # Use final template

    template = EMAIL_TEMPLATES[template_key]

    first_name = lead.company_name.split()[0] if lead.company_name else "there"
    demo_link = f"https://app.primehaul.co.uk/signup?ref={lead.email.split('@')[0]}"

    subject = template["subject"]
    body = template["body"].format(
        first_name=first_name,
        demo_link=demo_link
    )

    success, message_id = send_outreach_email(lead.email, subject, body)

    if success:
        outreach_email = OutreachEmail(
            lead_id=lead.id,
            direction="sent",
            subject=subject,
            body=body,
            message_id=message_id,
        )
        db.add(outreach_email)

        lead.emails_sent = emails_sent + 1
        lead.last_contacted = datetime.utcnow()

        # Set next followup
        if lead.emails_sent >= 3:
            lead.status = "dead"
            lead.next_followup = None
        else:
            lead.next_followup = datetime.utcnow() + timedelta(days=4)

        db.commit()
        return True

    return False


def run_automation_cycle(db: Session) -> Dict:
    """
    Run one cycle of the automation:
    1. Check for replies
    2. Send auto-replies where appropriate
    3. Send initial emails to new leads
    4. Send follow-ups where due

    Returns stats
    """
    stats = {
        "replies_found": 0,
        "auto_replies_sent": 0,
        "initial_emails_sent": 0,
        "followups_sent": 0,
        "errors": []
    }

    # 1. Check for replies
    try:
        replies = check_for_replies(db, since_hours=24)
        stats["replies_found"] = len(replies)

        # 2. Send auto-replies (only for positive/question, not negative)
        for reply in replies:
            lead = db.query(Lead).filter(Lead.id == reply["lead_id"]).first()
            if not lead:
                continue

            if reply["sentiment"] in ["positive", "question", "neutral"]:
                subject, body = generate_auto_reply(lead, reply["body"], reply["sentiment"])
                success, _ = send_outreach_email(lead.email, subject, body)
                if success:
                    stats["auto_replies_sent"] += 1

                    # Update lead status
                    if reply["sentiment"] == "positive":
                        lead.status = "interested"
                    db.commit()

    except Exception as e:
        stats["errors"].append(f"Reply check error: {e}")

    # 3. Send initial emails (max 5 per cycle to avoid spam)
    try:
        new_leads = get_leads_to_contact(db, limit=5)
        for lead in new_leads:
            if send_initial_email(lead, db):
                stats["initial_emails_sent"] += 1
    except Exception as e:
        stats["errors"].append(f"Initial email error: {e}")

    # 4. Send follow-ups (max 5 per cycle)
    try:
        followup_leads = get_leads_for_followup(db, limit=5)
        for lead in followup_leads:
            if send_followup_email(lead, db):
                stats["followups_sent"] += 1
    except Exception as e:
        stats["errors"].append(f"Followup error: {e}")

    return stats


# ============================================
# DASHBOARD STATS
# ============================================

def get_pipeline_stats(db: Session) -> Dict:
    """Get stats for the dashboard"""
    from sqlalchemy import func

    total = db.query(func.count(Lead.id)).scalar() or 0
    new = db.query(func.count(Lead.id)).filter(Lead.status == "new").scalar() or 0
    contacted = db.query(func.count(Lead.id)).filter(Lead.status == "contacted").scalar() or 0
    replied = db.query(func.count(Lead.id)).filter(Lead.status == "replied").scalar() or 0
    interested = db.query(func.count(Lead.id)).filter(Lead.status == "interested").scalar() or 0
    signed_up = db.query(func.count(Lead.id)).filter(Lead.status == "signed_up").scalar() or 0
    dead = db.query(func.count(Lead.id)).filter(Lead.status == "dead").scalar() or 0

    return {
        "total": total,
        "new": new,
        "contacted": contacted,
        "replied": replied,
        "interested": interested,
        "signed_up": signed_up,
        "dead": dead,
        "response_rate": round((replied + interested) / max(contacted, 1) * 100, 1),
        "conversion_rate": round(signed_up / max(total, 1) * 100, 1),
    }


def get_recent_activity(db: Session, limit: int = 20) -> List[Dict]:
    """Get recent email activity"""
    emails = db.query(OutreachEmail).order_by(
        OutreachEmail.sent_at.desc()
    ).limit(limit).all()

    activity = []
    for e in emails:
        lead = db.query(Lead).filter(Lead.id == e.lead_id).first()
        activity.append({
            "id": str(e.id),
            "lead_name": lead.company_name if lead else "Unknown",
            "lead_email": lead.email if lead else "",
            "direction": e.direction,
            "subject": e.subject,
            "body_preview": (e.body or "")[:100] + "..." if e.body and len(e.body) > 100 else e.body,
            "sent_at": e.sent_at.isoformat() if e.sent_at else None,
        })

    return activity


def import_leads_from_csv(csv_content: str, db: Session) -> Dict:
    """Import leads from CSV content"""
    import csv
    from io import StringIO

    reader = csv.DictReader(StringIO(csv_content))

    imported = 0
    skipped = 0
    errors = []

    for row in reader:
        email = row.get('email', '').strip()
        if not email or '@' not in email:
            skipped += 1
            continue

        # Check if already exists
        existing = db.query(Lead).filter(Lead.email == email).first()
        if existing:
            skipped += 1
            continue

        try:
            lead = Lead(
                company_name=row.get('name', row.get('company_name', '')).strip(),
                email=email,
                phone=row.get('phone', '').strip(),
                website=row.get('website', '').strip(),
                location=row.get('location', '').strip(),
                source=row.get('source', 'CSV Import').strip(),
                status="new",
            )
            db.add(lead)
            imported += 1
        except Exception as e:
            errors.append(str(e))

    db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
    }
