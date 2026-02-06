#!/usr/bin/env python3
"""
Sales Automation Cron Job

Run this every 30 minutes via cron or Railway scheduled task:
    */30 * * * * cd /app && python scripts/run_sales_automation.py

Or run manually:
    python scripts/run_sales_automation.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app.database import SessionLocal
from app import outreach


def main():
    print("=" * 50)
    print("Sales Automation Cycle")
    print("=" * 50)

    # Check if automation is enabled
    if os.getenv("SALES_AUTOMATION", "false").lower() != "true":
        print("⚠️  SALES_AUTOMATION is not enabled. Set SALES_AUTOMATION=true to enable.")
        print("Running in dry-run mode (no emails will be sent)...")
        return

    # Check SMTP config
    if not os.getenv("SMTP_USER") or not os.getenv("SMTP_PASSWORD"):
        print("❌ SMTP not configured. Set SMTP_USER and SMTP_PASSWORD.")
        return

    db = SessionLocal()

    try:
        stats = outreach.run_automation_cycle(db)

        print(f"\n✅ Cycle Complete:")
        print(f"   - Replies found: {stats['replies_found']}")
        print(f"   - Auto-replies sent: {stats['auto_replies_sent']}")
        print(f"   - Initial emails sent: {stats['initial_emails_sent']}")
        print(f"   - Follow-ups sent: {stats['followups_sent']}")

        if stats.get('errors'):
            print(f"\n⚠️  Errors:")
            for err in stats['errors']:
                print(f"   - {err}")

    except Exception as e:
        print(f"❌ Error running automation: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
