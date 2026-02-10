# PrimeHaul Go-Live Checklist

**Goal:** Professional launch-ready platform with proper email, legal compliance, and polished customer experience.

---

## PHASE 1: Professional Email Setup

### 1.1 Google Workspace Account

| Step | Action | Status |
|------|--------|--------|
| 1 | Go to https://workspace.google.com/business/signup/welcome | ☐ |
| 2 | Business name: `PrimeHaul` | ☐ |
| 3 | Number of employees: `Just you` | ☐ |
| 4 | Country: `United Kingdom` | ☐ |
| 5 | Current email: Your personal email for verification | ☐ |
| 6 | Domain: `primehaul.co.uk` (select "I have a domain") | ☐ |
| 7 | Create admin account: `jay@primehaul.co.uk` | ☐ |
| 8 | Plan: Business Starter (£4.60/month) | ☐ |
| 9 | Complete payment | ☐ |

### 1.2 DNS Records in Namecheap

Login to Namecheap → Domain List → primehaul.co.uk → Manage → Advanced DNS

**MX Records (Email Receiving)**

| Type | Host | Value | Priority | TTL |
|------|------|-------|----------|-----|
| MX | @ | aspmx.l.google.com | 1 | Automatic |
| MX | @ | alt1.aspmx.l.google.com | 5 | Automatic |
| MX | @ | alt2.aspmx.l.google.com | 5 | Automatic |
| MX | @ | alt3.aspmx.l.google.com | 10 | Automatic |
| MX | @ | alt4.aspmx.l.google.com | 10 | Automatic |

**SPF Record (Prevents Spam Flagging)**

| Type | Host | Value | TTL |
|------|------|-------|-----|
| TXT | @ | `v=spf1 include:_spf.google.com ~all` | Automatic |

**DKIM Record (Email Authentication)**

| Step | Action |
|------|--------|
| 1 | Google Admin Console → Apps → Google Workspace → Gmail |
| 2 | Click "Authenticate email" |
| 3 | Select primehaul.co.uk → Generate new record |
| 4 | Copy the TXT record value |
| 5 | Add to Namecheap as TXT record with host `google._domainkey` |

**DMARC Record (Email Policy)**

| Type | Host | Value | TTL |
|------|------|-------|-----|
| TXT | _dmarc | `v=DMARC1; p=quarantine; rua=mailto:jay@primehaul.co.uk` | Automatic |

### 1.3 Google App Password (for SMTP)

| Step | Action | Status |
|------|--------|--------|
| 1 | Go to https://myaccount.google.com | ☐ |
| 2 | Security → 2-Step Verification → Turn ON | ☐ |
| 3 | Complete 2FA setup with phone | ☐ |
| 4 | Security → 2-Step Verification → App passwords | ☐ |
| 5 | Select app: "Mail" | ☐ |
| 6 | Select device: "Other" → Enter "PrimeHaul SMTP" | ☐ |
| 7 | Click Generate | ☐ |
| 8 | **Copy the 16-character password** (shown once!) | ☐ |

### 1.4 Railway Environment Variables

Go to Railway Dashboard → PrimeHaul Project → Variables → Add these:

| Variable | Value |
|----------|-------|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `jay@primehaul.co.uk` |
| `SMTP_PASSWORD` | `xxxx xxxx xxxx xxxx` (your 16-char app password) |
| `IMAP_HOST` | `imap.gmail.com` |
| `IMAP_PORT` | `993` |
| `OUTREACH_EMAIL` | `jay@primehaul.co.uk` |
| `OUTREACH_NAME` | `Jay from PrimeHaul` |

### 1.5 Email Verification Test

| Test | How | Expected Result | Status |
|------|-----|-----------------|--------|
| Send test | Send email from jay@primehaul.co.uk to personal email | Delivered to inbox, not spam | ☐ |
| Receive test | Reply to that email | Appears in jay@primehaul.co.uk inbox | ☐ |
| SPF check | https://mxtoolbox.com/spf.aspx → Enter primehaul.co.uk | "SPF Record Found" | ☐ |
| DKIM check | https://mxtoolbox.com/dkim.aspx → Domain + selector "google" | "DKIM Record Found" | ☐ |
| DMARC check | https://mxtoolbox.com/dmarc.aspx → Enter primehaul.co.uk | "DMARC Record Found" | ☐ |
| Deliverability | https://www.mail-tester.com → Send email to their test address | Score 9/10 or higher | ☐ |

---

## PHASE 2: Legal & Compliance

### 2.1 ICO Registration (MANDATORY for UK)

| Step | Action | Status |
|------|--------|--------|
| 1 | Go to https://ico.org.uk/for-organisations/register/ | ☐ |
| 2 | Click "Register as fee payer" | ☐ |
| 3 | Organisation type: "Sole trader" or "Limited company" | ☐ |
| 4 | Trading name: `PrimeHaul` | ☐ |
| 5 | Address: Your registered business address | ☐ |
| 6 | Data controller contact: Your name | ☐ |
| 7 | Nature of work: "Software/IT services" | ☐ |
| 8 | Processing purposes: "Customer management", "Marketing" | ☐ |
| 9 | Pay fee: **£40/year** (Tier 1 for small orgs) | ☐ |
| 10 | Save registration number (format: ZA######) | ☐ |
| 11 | Add to website footer: "ICO Registered: ZA######" | ☐ |

### 2.2 Business Registration Check

| Item | Required? | Status |
|------|-----------|--------|
| Sole trader registered with HMRC | Yes if not Ltd | ☐ |
| OR Ltd company registered at Companies House | Alternative | ☐ |
| Business bank account | Recommended | ☐ |
| VAT registration | Only if revenue > £85k/year | ☐ |

### 2.3 Legal Pages Audit

Your legal pages exist at `/terms` and `/privacy`. Verify they include:

**Terms of Service (`/terms`)**

| Section | Included | Status |
|---------|----------|--------|
| Service description | ☐ | |
| Account registration requirements | ☐ | |
| Prepaid credits billing model explained | ☐ | |
| 3 free credits on signup | ☐ | |
| Credit pack pricing (£99-£699) | ☐ | |
| AI-generated quotes disclaimer | ☐ | |
| Limitation of liability | ☐ | |
| Termination terms | ☐ | |
| Governing law: England and Wales | ☐ | |
| Contact email for disputes | ☐ | |

**Privacy Policy (`/privacy`)**

| Section | Included | Status |
|---------|----------|--------|
| Data controller: PrimeHaul / Jaybo | ☐ | |
| What data collected (companies + customers) | ☐ | |
| How data is used | ☐ | |
| Third parties: Stripe, OpenAI, Mapbox, Railway | ☐ | |
| Data retention periods | ☐ | |
| UK GDPR rights (access, erasure, portability) | ☐ | |
| How to make a data request | ☐ | |
| Contact: privacy@primehaul.co.uk | ☐ | |
| ICO registration number | ☐ | |
| Cookie usage | ☐ | |

### 2.4 Website Footer Update

Add to landing page and all public pages:

```
© 2026 PrimeHaul — An intelligent move.
ICO Registered: ZA###### | Terms | Privacy
```

---

## PHASE 3: Stripe Production Setup

### 3.1 Switch to Live Mode

| Step | Action | Status |
|------|--------|--------|
| 1 | Stripe Dashboard → Activate your account | ☐ |
| 2 | Complete business verification (ID, address proof) | ☐ |
| 3 | Add bank account for payouts | ☐ |
| 4 | Enable live mode toggle (top-right) | ☐ |
| 5 | Create live credit pack products + prices | ☐ |

### 3.2 Live API Keys

| Step | Action | Status |
|------|--------|--------|
| 1 | Developers → API Keys → Reveal live secret key | ☐ |
| 2 | Copy `sk_live_...` secret key | ☐ |
| 3 | Copy `pk_live_...` publishable key | ☐ |
| 4 | Update Railway env vars with live keys | ☐ |

### 3.3 Live Webhook

| Step | Action | Status |
|------|--------|--------|
| 1 | Developers → Webhooks → Add endpoint | ☐ |
| 2 | URL: `https://primehaul.co.uk/billing/webhook` | ☐ |
| 3 | Events: `checkout.session.completed`, `invoice.paid`, `customer.subscription.*` | ☐ |
| 4 | Copy webhook signing secret | ☐ |
| 5 | Update `STRIPE_WEBHOOK_SECRET` in Railway | ☐ |

### 3.4 Credit Pack Prices (Live)

Create these products in Stripe live mode:

| Product | Price | Price ID |
|---------|-------|----------|
| Starter Pack (10 credits) | £99 | price_live_... |
| Growth Pack (25 credits) | £225 | price_live_... |
| Pro Pack (50 credits) | £399 | price_live_... |
| Enterprise Pack (100 credits) | £699 | price_live_... |

Update price IDs in your code/environment if hardcoded.

---

## PHASE 4: Platform Polish

### 4.1 Branding Consistency Check

| Page | Logo | Slogan | Colors | Status |
|------|------|--------|--------|--------|
| Landing page | ☐ | ☐ | ☐ | |
| Login page | ☐ | ☐ | ☐ | |
| Signup page | ☐ | ☐ | ☐ | |
| Customer survey (all screens) | ☐ | ☐ | ☐ | |
| Admin dashboard | ☐ | ☐ | ☐ | |
| Quote emails | ☐ | ☐ | ☐ | |
| Terms & Privacy pages | ☐ | ☐ | ☐ | |

### 4.2 Contact Information

Create these email aliases in Google Workspace:

| Email | Purpose | Status |
|-------|---------|--------|
| jay@primehaul.co.uk | Main contact, sales | ☐ |
| support@primehaul.co.uk | Customer support (alias to jay@) | ☐ |
| privacy@primehaul.co.uk | GDPR requests (alias to jay@) | ☐ |
| enterprise@primehaul.co.uk | Enterprise inquiries (alias to jay@) | ☐ |

### 4.3 Error Page Check

| Error | URL to Test | Shows Branded Page | Status |
|-------|-------------|-------------------|--------|
| 404 Not Found | /nonexistent-page | ☐ | |
| Trial Expired | (simulate) | ☐ | |
| Subscription Expired | (simulate) | ☐ | |

### 4.4 Mobile Testing

Test the full survey flow on:

| Device | Browser | Flow Completes | Status |
|--------|---------|----------------|--------|
| iPhone | Safari | ☐ | |
| iPhone | Chrome | ☐ | |
| Android | Chrome | ☐ | |
| iPad | Safari | ☐ | |

---

## PHASE 5: Pre-Launch Testing

### 5.1 Full Customer Flow Test

| Step | Action | Works | Status |
|------|--------|-------|--------|
| 1 | Create test company account | ☐ | |
| 2 | Generate survey link from dashboard | ☐ | |
| 3 | Open link in incognito/mobile | ☐ | |
| 4 | Complete full survey (locations, property, rooms, photos) | ☐ | |
| 5 | Submit quote for review | ☐ | |
| 6 | Check quote appears in admin dashboard | ☐ | |
| 7 | Approve quote with final price | ☐ | |
| 8 | Verify customer sees approved quote | ☐ | |
| 9 | Test credit deduction (3 free → 2 remaining) | ☐ | |

### 5.2 Payment Flow Test

| Step | Action | Works | Status |
|------|--------|-------|--------|
| 1 | Use up 3 free credits | ☐ | |
| 2 | Low credits warning appears | ☐ | |
| 3 | Click "Buy Credits" | ☐ | |
| 4 | Stripe Checkout loads | ☐ | |
| 5 | Complete test payment (use Stripe test card 4242...) | ☐ | |
| 6 | Credits added to account | ☐ | |
| 7 | Receipt email received | ☐ | |

### 5.3 Email Delivery Test

| Email Type | Trigger | Delivered | Not Spam | Status |
|------------|---------|-----------|----------|--------|
| Survey invite | Dashboard "Send Invite" | ☐ | ☐ | |
| Quote submitted notification | Customer submits | ☐ | ☐ | |
| Quote approved notification | Admin approves | ☐ | ☐ | |
| Cold outreach email 1 | Sales automation | ☐ | ☐ | |

---

## PHASE 6: Launch Prep

### 6.1 First Customer Targets (Ready to Contact)

You have 17 leads ready. Prioritize by location:

**Tier 1 — London (High Volume)**

| Company | Email | Priority |
|---------|-------|----------|
| Kiwi Movers | quote@kiwimovers.co.uk | High |
| Fox Moving | info@fox-moving.com | High |
| MTC Removals | info@mtcremovals.com | High |
| We Move Anything | enquiries@wemoveanything.com | Medium |
| Big Van World | sales@bigvanworld.co.uk | Medium |
| Get A Mover | info@getamover.co.uk | Medium |
| Quick Wasters | info@quickwasters.co.uk | Low |

**Tier 2 — Major Cities**

| Company | Email | Location |
|---------|-------|----------|
| Man With A Van Manchester | info@manwithavanremovalsmanchester.co.uk | Manchester |
| Burke Bros Moving | sales@burkebros.co.uk | Manchester |
| A Star Removals | info@astarremovals.co.uk | Manchester |
| Complete Removals | sales@completeremovals.co.uk | Birmingham |
| Britannia Leeds | info@britanniaturnbulls.co.uk | Leeds |

**Tier 3 — Regional**

| Company | Email | Location |
|---------|-------|----------|
| Near & Far Removals | enquiries@nearandfarremovals.co.uk | Nottingham |
| Clark & Rose | moving@clarkandrose.co.uk | Edinburgh |
| White & Company | hq@whiteandcompany.co.uk | Southampton |
| Moveme | hello@viewmychain.com | Brighton |
| Abels Moving | enquiries@abels.co.uk | Cambridge |

### 6.2 Email Sequence Schedule

| Day | Action | Template |
|-----|--------|----------|
| Day 0 | Send Email 1 to all 17 leads | "Quick one for {company_name}" |
| Day 1-2 | Monitor for replies | — |
| Day 3 | Send Email 2 to non-responders | "Re: Quick one for {company_name}" |
| Day 4-6 | Handle replies, book demos | — |
| Day 7 | Send Email 3 to non-responders | "Last one (then I'll leave you alone)" |
| Day 8+ | Focus on warm leads only | — |

### 6.3 Demo Script Prep

When a lead responds positively, be ready:

| Item | Prepared | Status |
|------|----------|--------|
| Demo company account created | ☐ | |
| Sample survey link ready | ☐ | |
| 5-minute walkthrough script | ☐ | |
| Pricing one-pager | ☐ | |
| "Getting Started" email template | ☐ | |

---

## PHASE 7: Post-Launch Monitoring

### 7.1 Daily Checks (First Week)

| Check | Where | Status |
|-------|-------|--------|
| Railway deployment status | Railway Dashboard | ☐ |
| Error logs | Railway Logs | ☐ |
| New signups | Superadmin Dashboard | ☐ |
| Survey completions | Superadmin Dashboard | ☐ |
| Email bounces | Google Workspace | ☐ |
| Stripe payments | Stripe Dashboard | ☐ |

### 7.2 Metrics to Track

| Metric | Target (Month 1) |
|--------|------------------|
| Cold emails sent | 50+ |
| Email open rate | 40%+ |
| Demo requests | 5+ |
| Signups | 3+ |
| Paid conversions | 1+ |

---

## FINAL CHECKLIST SUMMARY

### Before Sending First Email

| Category | Items | Complete |
|----------|-------|----------|
| Email Setup | Google Workspace, DNS, SMTP, tested | ☐ |
| Legal | ICO registered, Terms/Privacy live | ☐ |
| Stripe | Live mode, webhook, products created | ☐ |
| Platform | Full flow tested, mobile tested | ☐ |
| Branding | Consistent everywhere, slogan visible | ☐ |

### Go-Live Approval

| Checkpoint | Verified By | Date |
|------------|-------------|------|
| All emails deliver to inbox (not spam) | | |
| Payment flow works end-to-end | | |
| Survey flow works on mobile | | |
| ICO registration number received | | |
| First cold email ready to send | | |

---

**When all boxes are ticked, you're ready to launch.**

*PrimeHaul — An intelligent move.*
