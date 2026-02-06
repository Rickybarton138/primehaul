"""
Activity Tracker - Comprehensive user behavior tracking for product insights

Tracks:
- Page views with time spent
- Button clicks and interactions
- Form submissions (success/failure)
- Feature usage patterns
- Session flows (user journey)
- Friction points (where users get stuck/leave)

This data feeds into:
1. Superadmin dashboard (real-time boss activity)
2. AI pattern detection (identify UX issues)
3. Product improvement suggestions
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, text
import json

from app.models import UsageAnalytics, UserInteraction, Company

logger = logging.getLogger(__name__)


# ============================================================================
# EVENT TYPES - Standardized event taxonomy
# ============================================================================

EVENT_TYPES = {
    # Page Views
    "page_view": "User viewed a page",
    "page_exit": "User left a page",

    # Survey Flow (Customer)
    "survey_started": "Customer started survey",
    "survey_step_completed": "Customer completed a survey step",
    "survey_abandoned": "Customer abandoned survey",
    "survey_submitted": "Customer submitted survey",
    "photo_uploaded": "Customer uploaded a photo",
    "photo_deleted": "Customer deleted a photo",
    "room_added": "Customer added a room",
    "room_deleted": "Customer deleted a room",
    "item_edited": "Customer edited an item",
    "address_entered": "Customer entered address",
    "contact_entered": "Customer entered contact details",

    # Boss Actions
    "boss_login": "Boss logged in",
    "boss_dashboard_view": "Boss viewed dashboard",
    "boss_job_view": "Boss viewed a job",
    "boss_job_approved": "Boss approved a job",
    "boss_job_rejected": "Boss rejected a job",
    "boss_quick_approved": "Boss quick-approved from dashboard",
    "boss_price_edited": "Boss edited price",
    "boss_note_added": "Boss added internal note",
    "boss_settings_changed": "Boss changed settings",
    "boss_link_generated": "Boss generated survey link",
    "boss_link_copied": "Boss copied survey link",
    "boss_link_shared": "Boss shared survey link",

    # Feature Usage
    "feature_used": "User used a specific feature",
    "feature_ignored": "User skipped/ignored a feature",
    "help_requested": "User looked for help",

    # Errors & Friction
    "error_occurred": "An error occurred",
    "form_validation_failed": "Form validation failed",
    "session_timeout": "Session timed out",
    "rage_click": "User clicked rapidly (frustration)",
    "long_pause": "User paused for extended time (confusion)",
}


# ============================================================================
# TRACKING FUNCTIONS
# ============================================================================

def track_activity(
    db: Session,
    company_id: Optional[str],
    event_type: str,
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    user_type: str = "unknown",  # "boss", "customer", "visitor"
    page_url: Optional[str] = None,
    referrer: Optional[str] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    duration_seconds: Optional[int] = None
) -> UsageAnalytics:
    """
    Track any user activity event.

    Args:
        db: Database session
        company_id: Company UUID (if known)
        event_type: Type of event (from EVENT_TYPES)
        metadata: Additional event data
        session_id: Browser session identifier
        user_type: "boss", "customer", or "visitor"
        page_url: Current page URL
        referrer: Previous page URL
        user_agent: Browser user agent
        ip_address: User IP (for geo/device info)
        duration_seconds: Time spent (for page_exit events)

    Returns:
        Created UsageAnalytics
    """
    try:
        # Build comprehensive metadata
        full_metadata = {
            "session_id": session_id,
            "user_type": user_type,
            "page_url": page_url,
            "referrer": referrer,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "duration_seconds": duration_seconds,
            "timestamp_iso": datetime.utcnow().isoformat(),
            **(metadata or {})
        }

        # Remove None values
        full_metadata = {k: v for k, v in full_metadata.items() if v is not None}

        event = UsageAnalytics(
            company_id=company_id,
            event_type=event_type,
            event_metadata=full_metadata
        )
        db.add(event)
        db.commit()

        logger.debug(f"Tracked: {event_type} for company {company_id}")
        return event

    except Exception as e:
        logger.error(f"Failed to track activity: {e}")
        db.rollback()
        return None


def track_page_view(
    db: Session,
    company_id: Optional[str],
    page_url: str,
    user_type: str = "unknown",
    session_id: Optional[str] = None,
    referrer: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """Track a page view."""
    return track_activity(
        db=db,
        company_id=company_id,
        event_type="page_view",
        user_type=user_type,
        page_url=page_url,
        session_id=session_id,
        referrer=referrer,
        metadata=metadata
    )


def track_boss_action(
    db: Session,
    company_id: str,
    action: str,
    metadata: Optional[Dict] = None,
    session_id: Optional[str] = None
):
    """Track a boss/admin action."""
    return track_activity(
        db=db,
        company_id=company_id,
        event_type=f"boss_{action}",
        user_type="boss",
        session_id=session_id,
        metadata=metadata
    )


def track_customer_action(
    db: Session,
    company_id: str,
    action: str,
    job_token: Optional[str] = None,
    metadata: Optional[Dict] = None,
    session_id: Optional[str] = None
):
    """Track a customer action during survey."""
    meta = {"job_token": job_token, **(metadata or {})}
    return track_activity(
        db=db,
        company_id=company_id,
        event_type=action,
        user_type="customer",
        session_id=session_id,
        metadata=meta
    )


def track_friction(
    db: Session,
    company_id: Optional[str],
    friction_type: str,
    page_url: str,
    details: Optional[Dict] = None,
    session_id: Optional[str] = None
):
    """
    Track friction points (where users struggle).

    friction_type: "rage_click", "long_pause", "error", "abandonment", "form_retry"
    """
    return track_activity(
        db=db,
        company_id=company_id,
        event_type=f"friction_{friction_type}",
        page_url=page_url,
        session_id=session_id,
        metadata={"friction_type": friction_type, **(details or {})}
    )


# ============================================================================
# ANALYTICS QUERIES - For Superadmin Dashboard
# ============================================================================

def get_live_boss_activity(db: Session, minutes: int = 30) -> List[Dict]:
    """
    Get recent boss activity across all companies.
    Returns live feed for superadmin dashboard.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    events = db.query(UsageAnalytics).filter(
        UsageAnalytics.recorded_at >= cutoff,
        UsageAnalytics.event_type.like("boss_%")
    ).order_by(UsageAnalytics.recorded_at.desc()).limit(50).all()

    result = []
    for e in events:
        company = db.query(Company).filter(Company.id == e.company_id).first()
        meta = e.event_metadata or {}

        # Calculate time ago
        delta = datetime.utcnow() - e.recorded_at.replace(tzinfo=None)
        if delta.seconds < 60:
            time_ago = "just now"
        elif delta.seconds < 3600:
            time_ago = f"{delta.seconds // 60}m ago"
        else:
            time_ago = f"{delta.seconds // 3600}h ago"

        result.append({
            "id": str(e.id),
            "company_name": company.company_name if company else "Unknown",
            "company_slug": company.slug if company else "",
            "event_type": e.event_type,
            "event_label": EVENT_TYPES.get(e.event_type, e.event_type.replace("_", " ").title()),
            "time_ago": time_ago,
            "timestamp": e.recorded_at.isoformat(),
            "metadata": meta,
            "page_url": meta.get("page_url"),
            "job_token": meta.get("job_token"),
        })

    return result


def get_session_flow(db: Session, session_id: str) -> List[Dict]:
    """
    Get the complete journey for a session.
    Shows every page/action in order.
    """
    events = db.query(UsageAnalytics).filter(
        UsageAnalytics.event_metadata.contains({"session_id": session_id})
    ).order_by(UsageAnalytics.recorded_at.asc()).all()

    return [
        {
            "event_type": e.event_type,
            "timestamp": e.recorded_at.isoformat(),
            "page_url": (e.event_metadata or {}).get("page_url"),
            "duration": (e.event_metadata or {}).get("duration_seconds"),
        }
        for e in events
    ]


def get_funnel_analytics(db: Session, company_id: Optional[str] = None, days: int = 7) -> Dict:
    """
    Get funnel conversion rates.
    Shows where users drop off in the survey flow.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    base_query = db.query(UsageAnalytics).filter(
        UsageAnalytics.recorded_at >= cutoff
    )
    if company_id:
        base_query = base_query.filter(UsageAnalytics.company_id == company_id)

    # Count events at each stage
    funnel_stages = [
        ("survey_started", "Started Survey"),
        ("address_entered", "Entered Address"),
        ("room_added", "Added First Room"),
        ("photo_uploaded", "Uploaded Photos"),
        ("contact_entered", "Entered Contact"),
        ("survey_submitted", "Submitted"),
    ]

    results = {}
    for event_type, label in funnel_stages:
        count = base_query.filter(UsageAnalytics.event_type == event_type).count()
        results[event_type] = {"label": label, "count": count}

    # Calculate drop-off rates
    prev_count = None
    for event_type, _ in funnel_stages:
        if prev_count is not None and prev_count > 0:
            current = results[event_type]["count"]
            results[event_type]["drop_off_rate"] = round((1 - current / prev_count) * 100, 1)
            results[event_type]["conversion_rate"] = round((current / prev_count) * 100, 1)
        prev_count = results[event_type]["count"]

    return results


def get_friction_hotspots(db: Session, days: int = 7) -> List[Dict]:
    """
    Identify pages/features with high friction.
    Based on rage clicks, long pauses, errors, abandonment.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    friction_events = db.query(UsageAnalytics).filter(
        UsageAnalytics.recorded_at >= cutoff,
        UsageAnalytics.event_type.like("friction_%")
    ).all()

    # Aggregate by page
    page_friction = {}
    for e in friction_events:
        page = (e.event_metadata or {}).get("page_url", "unknown")
        if page not in page_friction:
            page_friction[page] = {"count": 0, "types": {}}
        page_friction[page]["count"] += 1

        friction_type = (e.event_metadata or {}).get("friction_type", "unknown")
        page_friction[page]["types"][friction_type] = page_friction[page]["types"].get(friction_type, 0) + 1

    # Sort by friction count
    hotspots = [
        {"page": page, **data}
        for page, data in sorted(page_friction.items(), key=lambda x: -x[1]["count"])
    ]

    return hotspots[:10]  # Top 10 friction hotspots


def get_feature_usage(db: Session, days: int = 7) -> Dict:
    """
    Track which features are being used vs ignored.
    Helps identify underused features.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    features = [
        "boss_link_generated",
        "boss_link_copied",
        "boss_link_shared",
        "boss_quick_approved",
        "boss_price_edited",
        "boss_note_added",
        "boss_settings_changed",
    ]

    usage = {}
    for feature in features:
        count = db.query(UsageAnalytics).filter(
            UsageAnalytics.recorded_at >= cutoff,
            UsageAnalytics.event_type == feature
        ).count()
        usage[feature] = {
            "label": feature.replace("boss_", "").replace("_", " ").title(),
            "count": count
        }

    return usage


def get_company_engagement(db: Session, days: int = 7) -> List[Dict]:
    """
    Rank companies by engagement level.
    Shows most/least active companies.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Count events per company
    results = db.query(
        UsageAnalytics.company_id,
        func.count(UsageAnalytics.id).label("event_count")
    ).filter(
        UsageAnalytics.recorded_at >= cutoff,
        UsageAnalytics.company_id.isnot(None)
    ).group_by(UsageAnalytics.company_id).order_by(
        func.count(UsageAnalytics.id).desc()
    ).limit(20).all()

    engagement = []
    for company_id, count in results:
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            engagement.append({
                "company_name": company.company_name,
                "company_slug": company.slug,
                "event_count": count,
                "engagement_level": "high" if count > 50 else "medium" if count > 20 else "low"
            })

    return engagement


# ============================================================================
# AI INSIGHTS - Pattern Detection & Suggestions
# ============================================================================

def analyze_patterns_and_suggest(db: Session) -> List[Dict]:
    """
    AI-powered analysis of user behavior patterns.
    Returns actionable suggestions for product improvement.

    This is the foundation for the self-evolving system.
    """
    suggestions = []

    # 1. Check funnel drop-offs
    funnel = get_funnel_analytics(db, days=7)
    for stage, data in funnel.items():
        if data.get("drop_off_rate", 0) > 40:
            suggestions.append({
                "type": "funnel_drop_off",
                "severity": "high" if data["drop_off_rate"] > 60 else "medium",
                "stage": stage,
                "drop_off_rate": data["drop_off_rate"],
                "suggestion": f"High drop-off at '{data['label']}' stage ({data['drop_off_rate']}%). Consider simplifying this step or adding guidance.",
                "auto_fixable": False
            })

    # 2. Check friction hotspots
    hotspots = get_friction_hotspots(db, days=7)
    for hotspot in hotspots[:3]:  # Top 3
        if hotspot["count"] > 5:
            suggestions.append({
                "type": "friction_hotspot",
                "severity": "high" if hotspot["count"] > 20 else "medium",
                "page": hotspot["page"],
                "friction_count": hotspot["count"],
                "friction_types": hotspot["types"],
                "suggestion": f"Page '{hotspot['page']}' has high friction ({hotspot['count']} events). Most common: {list(hotspot['types'].keys())}",
                "auto_fixable": False
            })

    # 3. Check underused features
    usage = get_feature_usage(db, days=7)
    for feature, data in usage.items():
        if data["count"] == 0:
            suggestions.append({
                "type": "unused_feature",
                "severity": "low",
                "feature": feature,
                "suggestion": f"Feature '{data['label']}' hasn't been used in 7 days. Consider making it more prominent or removing it.",
                "auto_fixable": False
            })

    # 4. Check for rage clicks (frustration)
    rage_clicks = db.query(UsageAnalytics).filter(
        UsageAnalytics.event_type == "friction_rage_click",
        UsageAnalytics.recorded_at >= datetime.utcnow() - timedelta(days=7)
    ).count()

    if rage_clicks > 10:
        suggestions.append({
            "type": "user_frustration",
            "severity": "high",
            "rage_click_count": rage_clicks,
            "suggestion": f"Detected {rage_clicks} rage click events. Users are frustrated with UI responsiveness or clarity.",
            "auto_fixable": False
        })

    return suggestions
