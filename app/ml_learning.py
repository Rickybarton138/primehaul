"""
Self-Learning ML Module for PrimeHaul

Analyzes user feedback (corrections) and learns patterns to automatically
improve future AI detections. This creates a feedback loop where the more
the system is used, the smarter it gets.

How it works:
1. Users correct AI detections (e.g., "3-seater sofa" → "2-seater sofa")
2. These corrections are stored in ItemFeedback table
3. This module analyzes patterns in the feedback
4. Patterns with high confidence are auto-applied to future detections
5. The AI prompt is enhanced with learned knowledge
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models import ItemFeedback, LearnedCorrection

logger = logging.getLogger(__name__)

# Minimum samples needed before we start learning from a pattern
MIN_SAMPLES_FOR_LEARNING = 2

# Confidence threshold for auto-applying corrections
AUTO_APPLY_CONFIDENCE = 0.70  # 70% of the time users make this correction


def normalize_name(name: str) -> str:
    """Normalize item name for pattern matching"""
    if not name:
        return ""
    return name.lower().strip()


def run_learning_cycle(db: Session) -> Dict:
    """
    Main learning function. Analyzes all feedback and updates learned patterns.
    Should be called periodically (e.g., after each survey submission, or on a schedule).

    Returns a summary of what was learned.
    """
    logger.info("Starting ML learning cycle...")

    results = {
        "patterns_analyzed": 0,
        "new_patterns_learned": 0,
        "patterns_updated": 0,
        "patterns_promoted_to_auto": 0,
        "learned_items": []
    }

    try:
        # Get all feedback grouped by AI detection pattern
        feedback_patterns = db.query(
            ItemFeedback.ai_detected_name,
            ItemFeedback.corrected_name,
            ItemFeedback.corrected_category,
            func.count(ItemFeedback.id).label('count'),
            func.avg(ItemFeedback.corrected_cbm).label('avg_cbm'),
            func.avg(ItemFeedback.corrected_weight).label('avg_weight')
        ).filter(
            ItemFeedback.ai_detected_name.isnot(None),
            ItemFeedback.corrected_name.isnot(None),
            ItemFeedback.feedback_type.in_(['correction', 'variant_change'])
        ).group_by(
            ItemFeedback.ai_detected_name,
            ItemFeedback.corrected_name,
            ItemFeedback.corrected_category
        ).all()

        results["patterns_analyzed"] = len(feedback_patterns)

        for pattern in feedback_patterns:
            ai_name = pattern.ai_detected_name
            corrected_name = pattern.corrected_name
            corrected_category = pattern.corrected_category
            count = pattern.count
            avg_cbm = pattern.avg_cbm
            avg_weight = pattern.avg_weight

            if count < MIN_SAMPLES_FOR_LEARNING:
                continue

            normalized_ai = normalize_name(ai_name)
            if not normalized_ai:
                continue

            # Calculate how often this AI detection gets corrected to this specific value
            total_times_seen = db.query(func.count(ItemFeedback.id)).filter(
                func.lower(ItemFeedback.ai_detected_name) == normalized_ai
            ).scalar() or 1

            confidence = min(count / total_times_seen, 1.0) if total_times_seen > 0 else 0

            # Check if we already have this learned pattern
            existing = db.query(LearnedCorrection).filter(
                LearnedCorrection.ai_pattern == normalized_ai
            ).first()

            now = datetime.utcnow()

            if existing:
                # Update existing pattern
                # If new correction is more common, update it
                if confidence > float(existing.confidence or 0):
                    existing.corrected_name = corrected_name
                    existing.corrected_category = corrected_category
                    existing.confidence = Decimal(str(round(confidence, 2)))
                    if avg_cbm:
                        existing.learned_cbm = Decimal(str(round(float(avg_cbm), 4)))
                    if avg_weight:
                        existing.learned_weight_kg = Decimal(str(round(float(avg_weight), 2)))

                existing.times_seen = total_times_seen
                existing.times_corrected = count
                existing.last_learned_at = now

                # Promote to auto-apply if confidence is high enough
                was_auto = existing.auto_apply
                existing.auto_apply = confidence >= AUTO_APPLY_CONFIDENCE

                if existing.auto_apply and not was_auto:
                    results["patterns_promoted_to_auto"] += 1
                    logger.info(f"Promoted to auto-apply: '{ai_name}' → '{corrected_name}' (confidence: {confidence:.0%})")

                results["patterns_updated"] += 1
            else:
                # Create new learned pattern
                learned = LearnedCorrection(
                    ai_pattern=normalized_ai,
                    corrected_name=corrected_name,
                    corrected_category=corrected_category,
                    times_seen=total_times_seen,
                    times_corrected=count,
                    confidence=Decimal(str(round(confidence, 2))),
                    auto_apply=confidence >= AUTO_APPLY_CONFIDENCE,
                    last_learned_at=now,
                    created_at=now
                )

                if avg_cbm:
                    learned.learned_cbm = Decimal(str(round(float(avg_cbm), 4)))
                if avg_weight:
                    learned.learned_weight_kg = Decimal(str(round(float(avg_weight), 2)))

                db.add(learned)
                results["new_patterns_learned"] += 1

                results["learned_items"].append({
                    "from": ai_name,
                    "to": corrected_name,
                    "confidence": f"{confidence:.0%}",
                    "auto_apply": confidence >= AUTO_APPLY_CONFIDENCE
                })

                logger.info(f"Learned new pattern: '{ai_name}' → '{corrected_name}' (confidence: {confidence:.0%})")

        db.commit()
        logger.info(f"Learning cycle complete: {results['new_patterns_learned']} new, {results['patterns_updated']} updated, {results['patterns_promoted_to_auto']} promoted to auto-apply")

    except Exception as e:
        logger.error(f"Learning cycle error: {str(e)}")
        db.rollback()
        results["error"] = str(e)

    return results


def apply_learned_corrections(items: List[Dict], db: Session) -> Tuple[List[Dict], List[Dict]]:
    """
    Apply learned corrections to a list of AI-detected items.

    Returns:
        - Updated items list with corrections applied
        - List of corrections that were applied (for transparency)
    """
    if not items:
        return items, []

    corrections_applied = []

    # Get all auto-apply patterns
    auto_patterns = db.query(LearnedCorrection).filter(
        LearnedCorrection.auto_apply == True
    ).all()

    # Build lookup dict for fast matching
    pattern_lookup = {p.ai_pattern: p for p in auto_patterns}

    for item in items:
        original_name = item.get("name", "")
        normalized = normalize_name(original_name)

        if normalized in pattern_lookup:
            learned = pattern_lookup[normalized]

            # Apply the learned correction
            correction_info = {
                "original": original_name,
                "corrected_to": learned.corrected_name,
                "confidence": float(learned.confidence or 0),
                "reason": f"Auto-corrected based on {learned.times_corrected} previous corrections"
            }

            item["name"] = learned.corrected_name
            item["auto_corrected"] = True
            item["original_ai_name"] = original_name

            if learned.corrected_category:
                item["item_category"] = learned.corrected_category

            if learned.learned_cbm:
                item["cbm"] = float(learned.learned_cbm)

            if learned.learned_weight_kg:
                item["weight_kg"] = float(learned.learned_weight_kg)

            corrections_applied.append(correction_info)
            logger.info(f"Auto-corrected: '{original_name}' → '{learned.corrected_name}'")

    return items, corrections_applied


def get_learned_patterns_for_prompt(db: Session, limit: int = 20) -> str:
    """
    Generate a prompt enhancement string based on learned patterns.
    This is injected into the AI vision prompt to improve future detections.
    """
    patterns = db.query(LearnedCorrection).filter(
        LearnedCorrection.confidence >= Decimal('0.5'),
        LearnedCorrection.times_corrected >= 2
    ).order_by(
        LearnedCorrection.confidence.desc()
    ).limit(limit).all()

    if not patterns:
        return ""

    lines = ["Based on user feedback, make these naming adjustments:"]
    for p in patterns:
        lines.append(f"- If you detect '{p.ai_pattern}', call it '{p.corrected_name}' instead")

    return "\n".join(lines)


def get_learning_stats(db: Session) -> Dict:
    """Get statistics about the learning system for superadmin dashboard"""
    total_patterns = db.query(LearnedCorrection).count()
    auto_apply_patterns = db.query(LearnedCorrection).filter(
        LearnedCorrection.auto_apply == True
    ).count()

    high_confidence = db.query(LearnedCorrection).filter(
        LearnedCorrection.confidence >= Decimal('0.8')
    ).count()

    recent_patterns = db.query(LearnedCorrection).order_by(
        LearnedCorrection.last_learned_at.desc()
    ).limit(10).all()

    return {
        "total_patterns": total_patterns,
        "auto_apply_patterns": auto_apply_patterns,
        "high_confidence_patterns": high_confidence,
        "recent_patterns": [
            {
                "from": p.ai_pattern,
                "to": p.corrected_name,
                "confidence": float(p.confidence or 0),
                "times_corrected": p.times_corrected,
                "auto_apply": p.auto_apply
            }
            for p in recent_patterns
        ]
    }
