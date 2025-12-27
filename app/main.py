import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, Request, Form, UploadFile, File, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import aiofiles

from app.ai_vision import extract_removal_inventory

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PrimeHaul OS", version="1.0.0")

# Security: Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Security: Add trusted host middleware (configure for production)
# Uncomment and configure for production:
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"])

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("app/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

STATE: dict[str, dict] = {}
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "primehaul2025")


def check_admin_auth(admin_session: str | None) -> bool:
    """Check if admin session is valid"""
    return admin_session == ADMIN_PASSWORD


def get_job(token: str) -> dict:
    job = STATE.get(token)
    if not job:
        job = {
            "token": token,
            "pickup": None,
            "dropoff": None,
            "property_type": None,
            "rooms": [],  # list of {"id": str, "name": str, "photos": [...], "items": [...]}
            "status": "in_progress",  # in_progress, awaiting_approval, approved, rejected
            "customer_email": None,
            "customer_phone": None,
            "customer_name": None,
            "created_at": datetime.now().isoformat(),
            "submitted_at": None,
            "approved_at": None,
            "rejected_at": None,
            "total_cbm": 0,
            "total_weight_kg": 0,
            "admin_notes": [],  # [{"timestamp": str, "note": str}]
            "custom_price_low": None,  # Override AI price
            "custom_price_high": None,  # Override AI price
        }
        STATE[token] = job
    return job


def find_room(job: dict, room_id: str) -> dict | None:
    for r in job.get("rooms", []):
        if r.get("id") == room_id:
            return r
    return None


@app.get("/", response_class=HTMLResponse)
def home():
    return RedirectResponse(url="/s/demo-token", status_code=302)


@app.get("/s/{token}", response_class=HTMLResponse)
def survey_start(request: Request, token: str):
    get_job(token)
    return templates.TemplateResponse("start.html", {
        "request": request,
        "token": token,
        "title": "PrimeHaul OS",
        "nav_title": "PrimeHaul OS",
        "back_url": None,
        "progress": None,
    })


@app.post("/s/{token}/start")
def survey_start_post(token: str):
    return RedirectResponse(url=f"/s/{token}/move", status_code=303)


@app.get("/s/{token}/move", response_class=HTMLResponse)
def move_get(request: Request, token: str):
    job = get_job(token)
    return templates.TemplateResponse("move_map.html", {
        "request": request,
        "token": token,
        "title": "Set your move — PrimeHaul OS",
        "nav_title": "Set your move",
        "back_url": f"/s/{token}",
        "progress": 25,
        "mapbox_token": os.getenv("MAPBOX_ACCESS_TOKEN", ""),
        "pickup": job["pickup"],
        "dropoff": job["dropoff"],
    })


@app.post("/s/{token}/move")
def move_post(
    token: str,
    pickup_label: str = Form(""),
    pickup_lat: str = Form(""),
    pickup_lng: str = Form(""),
    dropoff_label: str = Form(""),
    dropoff_lat: str = Form(""),
    dropoff_lng: str = Form(""),
):
    if not (pickup_label and pickup_lat and pickup_lng and dropoff_label and dropoff_lat and dropoff_lng):
        return RedirectResponse(url=f"/s/{token}/move?err=missing", status_code=303)

    try:
        p_lat = float(pickup_lat); p_lng = float(pickup_lng)
        d_lat = float(dropoff_lat); d_lng = float(dropoff_lng)
    except ValueError:
        return RedirectResponse(url=f"/s/{token}/move?err=coords", status_code=303)

    job = get_job(token)
    job["pickup"] = {"label": pickup_label, "lat": p_lat, "lng": p_lng}
    job["dropoff"] = {"label": dropoff_label, "lat": d_lat, "lng": d_lng}
    return RedirectResponse(url=f"/s/{token}/property", status_code=303)


@app.get("/s/{token}/property", response_class=HTMLResponse)
def property_get(request: Request, token: str):
    job = get_job(token)
    return templates.TemplateResponse("property_type.html", {
        "request": request,
        "token": token,
        "title": "Property — PrimeHaul OS",
        "nav_title": "Property",
        "back_url": f"/s/{token}/move",
        "progress": 50,
        "property_type": job["property_type"],
    })


@app.post("/s/{token}/property")
def property_post(token: str, property_type: str = Form(...)):
    job = get_job(token)
    job["property_type"] = property_type
    # ✅ Next: pick a room (tap once)
    return RedirectResponse(url=f"/s/{token}/rooms", status_code=303)


# ----------------------------
# ROOMS (tap to add)
# ----------------------------

@app.get("/s/{token}/rooms", response_class=HTMLResponse)
def rooms_get(request: Request, token: str):
    job = get_job(token)
    return templates.TemplateResponse("rooms_pick.html", {
        "request": request,
        "token": token,
        "title": "Rooms — PrimeHaul OS",
        "nav_title": "Rooms",
        "back_url": f"/s/{token}/property",
        "progress": 65,
        "rooms": job.get("rooms", []),
    })


@app.post("/s/{token}/rooms/add")
def rooms_add(token: str, room_name: str = Form(...)):
    job = get_job(token)
    rid = uuid.uuid4().hex[:10]
    job["rooms"].append({
        "id": rid,
        "name": room_name,
        "photos": [],
        "items": [],       # structured list: [{"name": str, "qty": int, "notes": str, "bulky": bool}]
        "summary": "",     # summary text
    })
    # ✅ Immediately go to scan items for this room
    return RedirectResponse(url=f"/s/{token}/room/{rid}", status_code=303)


# ----------------------------
# SCAN ITEMS (photos per room)
# ----------------------------

@app.get("/s/{token}/room/{room_id}", response_class=HTMLResponse)
def room_scan_get(request: Request, token: str, room_id: str):
    job = get_job(token)
    room = find_room(job, room_id)
    if not room:
        return RedirectResponse(url=f"/s/{token}/rooms", status_code=303)

    # Build items_json from structured items
    items_json = {
        "items": room.get("items", []),
        "summary": room.get("summary", "")
    }

    return templates.TemplateResponse("room_scan.html", {
        "request": request,
        "token": token,
        "title": f"{room['name']} — PrimeHaul OS",
        "nav_title": room["name"],
        "back_url": f"/s/{token}/rooms",
        "progress": 75,
        "room_id": room_id,
        "room_name": room["name"],
        "photos": room["photos"],
        "items_json": items_json,
    })


@app.post("/s/{token}/room/{room_id}/upload")
async def room_scan_upload(
    token: str,
    room_id: str,
    photos: list[UploadFile] = File(default=[]),
):
    job = get_job(token)
    room = find_room(job, room_id)
    if not room:
        return RedirectResponse(url=f"/s/{token}/rooms", status_code=303)

    if not photos:
        return RedirectResponse(url=f"/s/{token}/room/{room_id}?err=no_photos", status_code=303)

    # Save uploaded photos and track paths for AI analysis
    saved_paths = []
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif"}

    for f in photos:
        # Validate file type
        if f.content_type not in ALLOWED_TYPES:
            logger.warning(f"Rejected file with invalid type: {f.content_type}")
            continue

        # Generate unique filename
        ext = os.path.splitext(f.filename or "photo.jpg")[1] or ".jpg"
        fname = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = UPLOAD_DIR / fname

        # Save file with size validation
        try:
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                logger.warning(f"File {f.filename} exceeds size limit")
                continue

            async with aiofiles.open(file_path, 'wb') as out_file:
                await out_file.write(content)

            saved_paths.append(str(file_path))
            room["photos"].append({"filename": fname, "url": f"/static/uploads/{fname}"})
            logger.info(f"Saved photo: {fname}")
        except Exception as e:
            logger.error(f"Error saving photo {f.filename}: {e}")
            continue

    # Use AI to analyze photos and extract inventory
    if saved_paths:
        try:
            logger.info(f"Analyzing {len(saved_paths)} photos with AI vision...")
            inventory = extract_removal_inventory(saved_paths)

            # Store structured items
            if inventory.get("items"):
                # Append new items to existing ones (don't replace)
                room["items"].extend(inventory["items"])
                if inventory.get("summary"):
                    room["summary"] = inventory.get("summary", "")
                logger.info(f"AI detected {len(inventory['items'])} items")
            else:
                logger.warning("AI returned no items")

        except Exception as e:
            logger.error(f"AI vision error: {e}")

    return RedirectResponse(url=f"/s/{token}/room/{room_id}?saved=1", status_code=303)


@app.post("/s/{token}/room/{room_id}/upload-json")
async def room_scan_upload_json(
    token: str,
    room_id: str,
    photos: list[UploadFile] = File(default=[]),
):
    """JSON version of upload endpoint for AJAX calls"""
    job = get_job(token)
    room = find_room(job, room_id)
    if not room:
        return JSONResponse({"ok": False, "error": "Room not found"}, status_code=404)

    if not photos:
        return JSONResponse({"ok": False, "error": "No photos provided"}, status_code=400)

    # Save uploaded photos and track paths for AI analysis
    saved_paths = []
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic", "image/heif"}

    for f in photos:
        # Validate file type
        if f.content_type not in ALLOWED_TYPES:
            logger.warning(f"Rejected file with invalid type: {f.content_type}")
            continue

        # Generate unique filename
        ext = os.path.splitext(f.filename or "photo.jpg")[1] or ".jpg"
        fname = f"{uuid.uuid4().hex[:12]}{ext}"
        file_path = UPLOAD_DIR / fname

        # Save file with size validation
        try:
            content = await f.read()
            if len(content) > MAX_FILE_SIZE:
                logger.warning(f"File {f.filename} exceeds size limit")
                continue

            async with aiofiles.open(file_path, 'wb') as out_file:
                await out_file.write(content)

            saved_paths.append(str(file_path))
            room["photos"].append({"filename": fname, "url": f"/static/uploads/{fname}"})
            logger.info(f"Saved photo: {fname}")
        except Exception as e:
            logger.error(f"Error saving photo {f.filename}: {e}")
            continue

    # Use AI to analyze photos and extract inventory
    if saved_paths:
        try:
            logger.info(f"Analyzing {len(saved_paths)} photos with AI vision...")
            inventory = extract_removal_inventory(saved_paths)

            # Store structured items
            if inventory.get("items"):
                # Append new items to existing ones (don't replace)
                room["items"].extend(inventory["items"])
                if inventory.get("summary"):
                    room["summary"] = inventory.get("summary", "")
                logger.info(f"AI detected {len(inventory['items'])} items")

        except Exception as e:
            logger.error(f"AI vision error: {e}")

    # Return JSON response
    return JSONResponse({
        "ok": True,
        "photos": room["photos"],
        "items_json": {
            "items": room.get("items", []),
            "summary": room.get("summary", "")
        }
    })


@app.post("/s/{token}/room/{room_id}/confirm_items")
def room_confirm_items(token: str, room_id: str, request: Request):
    """Process confirmed items from the checklist form"""
    job = get_job(token)
    room = find_room(job, room_id)
    if not room:
        return RedirectResponse(url=f"/s/{token}/rooms", status_code=303)

    # This endpoint will be called with form data containing:
    # - summary: optional summary text
    # - For each item index: name_{idx}, qty_{idx}, notes_{idx}, bulky_{idx}, keep_{idx}
    # We'll process this in a future update for now just redirect

    return RedirectResponse(url=f"/s/{token}/rooms", status_code=303)


# ----------------------------
# REVIEW + QUOTE
# ----------------------------

@app.get("/s/{token}/review", response_class=HTMLResponse)
def review_get(request: Request, token: str):
    job = get_job(token)
    return templates.TemplateResponse("review_inventory.html", {
        "request": request,
        "token": token,
        "title": "Review — PrimeHaul OS",
        "nav_title": "Review",
        "back_url": f"/s/{token}/rooms",
        "progress": 90,
        "rooms": job.get("rooms", []),
    })


@app.post("/s/{token}/review/finish")
def review_finish(token: str):
    return RedirectResponse(url=f"/s/{token}/quote-preview", status_code=303)


def calculate_quote(job: dict) -> dict:
    """Calculate professional quote based on CBM, weight, and items"""
    total_items = 0
    bulky_items = 0
    fragile_items = 0
    total_cbm = 0
    total_weight_kg = 0

    for room in job.get("rooms", []):
        items = room.get("items", [])
        for item in items:
            qty = item.get("qty", 1)
            total_items += qty

            # CBM calculations
            cbm_per_item = item.get("cbm", 0)
            total_cbm += cbm_per_item * qty

            # Weight calculations
            weight_per_item = item.get("weight_kg", 0)
            total_weight_kg += weight_per_item * qty

            if item.get("bulky"):
                bulky_items += qty
            if item.get("fragile"):
                fragile_items += qty

    # Professional pricing based on CBM (industry standard)
    base_price = 250  # Base callout fee
    cbm_price = total_cbm * 35  # £35 per cubic meter (industry standard)
    bulky_surcharge = bulky_items * 25  # £25 per bulky item for extra handling
    fragile_surcharge = fragile_items * 15  # £15 per fragile item for packing

    # Weight-based pricing (if load is heavy)
    weight_price = 0
    if total_weight_kg > 1000:  # Over 1 tonne
        weight_price = (total_weight_kg - 1000) * 0.50  # 50p per kg over 1 tonne

    # Distance pricing (mock - would use actual Google Maps distance)
    distance_price = 120

    total = base_price + cbm_price + bulky_surcharge + fragile_surcharge + weight_price + distance_price

    # Add realistic variance for estimate range
    estimate_low = int(total * 0.90)
    estimate_high = int(total * 1.20)

    # Determine confidence based on completeness
    if total_items < 5 or total_cbm < 1:
        confidence = "Low - Need more photos"
    elif total_items < 20 or total_cbm < 5:
        confidence = "Medium"
    else:
        confidence = "High"

    # Update job with totals
    job["total_cbm"] = round(total_cbm, 2)
    job["total_weight_kg"] = round(total_weight_kg, 0)

    # Use custom prices if admin set them
    final_low = job.get("custom_price_low") or estimate_low
    final_high = job.get("custom_price_high") or estimate_high

    return {
        "estimate_low": final_low,
        "estimate_high": final_high,
        "ai_estimate_low": estimate_low,
        "ai_estimate_high": estimate_high,
        "has_custom_price": bool(job.get("custom_price_low")),
        "total_items": total_items,
        "bulky_items": bulky_items,
        "fragile_items": fragile_items,
        "total_cbm": round(total_cbm, 2),
        "total_weight_kg": round(total_weight_kg, 0),
        "confidence": confidence,
        "breakdown": {
            "base": base_price,
            "volume": round(cbm_price, 2),
            "bulky": bulky_surcharge,
            "fragile": fragile_surcharge,
            "weight": round(weight_price, 2),
            "distance": distance_price
        }
    }


@app.get("/s/{token}/quote-preview", response_class=HTMLResponse)
def quote_preview(request: Request, token: str):
    job = get_job(token)
    quote = calculate_quote(job)

    return templates.TemplateResponse("quote_preview.html", {
        "request": request,
        "token": token,
        "title": "Your Quote — PrimeHaul OS",
        "nav_title": "Your Quote",
        "back_url": f"/s/{token}/review",
        "progress": 100,
        "job": job,
        "estimate_low": quote["estimate_low"],
        "estimate_high": quote["estimate_high"],
        "total_items": quote["total_items"],
        "bulky_items": quote["bulky_items"],
        "fragile_items": quote["fragile_items"],
        "total_cbm": quote["total_cbm"],
        "total_weight_kg": quote["total_weight_kg"],
        "confidence": quote["confidence"],
        "breakdown": quote["breakdown"],
    })


@app.post("/s/{token}/submit-quote")
def submit_quote_redirect(token: str):
    """Redirect to contact form before final submission"""
    return RedirectResponse(url=f"/s/{token}/contact", status_code=303)


@app.get("/s/{token}/contact", response_class=HTMLResponse)
def customer_contact_form(request: Request, token: str):
    """Customer contact details form"""
    job = get_job(token)
    quote = calculate_quote(job)

    return templates.TemplateResponse("customer_contact.html", {
        "request": request,
        "token": token,
        "title": "Contact Details — PrimeHaul OS",
        "nav_title": "Contact Details",
        "back_url": f"/s/{token}/quote-preview",
        "progress": 100,
        "job": job,
        "estimate_low": quote["estimate_low"],
        "estimate_high": quote["estimate_high"],
        "total_items": quote["total_items"],
        "total_cbm": quote["total_cbm"],
    })


@app.post("/s/{token}/submit-contact")
def submit_contact_and_quote(
    token: str,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    customer_email: str = Form(...)
):
    """Final submission with contact details"""
    job = get_job(token)

    if not customer_name or not customer_phone or not customer_email:
        return RedirectResponse(url=f"/s/{token}/contact?err=required", status_code=303)

    # Save customer details
    job["customer_name"] = customer_name.strip()
    job["customer_phone"] = customer_phone.strip()
    job["customer_email"] = customer_email.strip()
    job["status"] = "awaiting_approval"
    job["submitted_at"] = datetime.now().isoformat()

    # TODO: Send email/SMS to removals company boss
    # TODO: Send confirmation to customer
    logger.info(f"Quote {token} submitted by {customer_name} ({customer_email}, {customer_phone}). CBM: {job.get('total_cbm')}, Weight: {job.get('total_weight_kg')}kg")

    return RedirectResponse(url=f"/s/{token}/quote-preview", status_code=303)


@app.get("/test-map", response_class=HTMLResponse)
def test_map(request: Request):
    token = os.getenv("MAPBOX_ACCESS_TOKEN", "")
    return templates.TemplateResponse("test_map.html", {
        "request": request,
        "title": "Test Map — PrimeHaul OS",
        "nav_title": "Test Map",
        "back_url": "/",
        "progress": None,
        "mapbox_token": token,
    })


# ============================================
# ADMIN ROUTES - Boss Approval Dashboard
# ============================================

@app.get("/admin", response_class=HTMLResponse)
def admin_login_page(request: Request, admin_session: str | None = Cookie(None)):
    """Admin login page - redirects to dashboard if already logged in"""
    if check_admin_auth(admin_session):
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "title": "Admin Login — PrimeHaul OS",
        "error": request.query_params.get("error"),
    })


@app.post("/admin/login")
def admin_login(password: str = Form(...)):
    """Handle admin login"""
    if password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        response.set_cookie(key="admin_session", value=ADMIN_PASSWORD, httponly=True, max_age=86400)  # 24 hours
        return response
    else:
        return RedirectResponse(url="/admin?error=invalid", status_code=303)


@app.get("/admin/logout")
def admin_logout():
    """Logout admin"""
    response = RedirectResponse(url="/admin", status_code=303)
    response.delete_cookie(key="admin_session")
    return response


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, admin_session: str | None = Cookie(None)):
    """Admin dashboard showing all jobs awaiting approval"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    # Get all jobs awaiting approval
    awaiting_jobs = []
    approved_jobs = []
    rejected_jobs = []

    for token, job in STATE.items():
        status = job.get("status", "in_progress")
        if status == "awaiting_approval":
            awaiting_jobs.append(job)
        elif status == "approved":
            approved_jobs.append(job)
        elif status == "rejected":
            rejected_jobs.append(job)

    # Sort by most recent first (mock - would use created_at timestamp)
    awaiting_jobs.reverse()
    approved_jobs.reverse()
    rejected_jobs.reverse()

    return templates.TemplateResponse("admin_dashboard_v2.html", {
        "request": request,
        "title": "Admin Dashboard — PrimeHaul OS",
        "awaiting_jobs": awaiting_jobs,
        "approved_jobs": approved_jobs[:10],  # Show last 10
        "rejected_jobs": rejected_jobs[:10],  # Show last 10
    })


@app.get("/admin/job/{token}", response_class=HTMLResponse)
def admin_job_review(request: Request, token: str, admin_session: str | None = Cookie(None)):
    """Detailed job review for admin"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    job = STATE.get(token)
    if not job:
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    quote = calculate_quote(job)

    return templates.TemplateResponse("admin_job_review_v2.html", {
        "request": request,
        "title": f"Review Job {token[:8]} — PrimeHaul OS",
        "token": token,
        "job": job,
        "quote": quote,
    })


@app.post("/admin/job/{token}/approve")
def admin_approve_job(token: str, admin_session: str | None = Cookie(None)):
    """Approve a job"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    job = STATE.get(token)
    if job:
        job["status"] = "approved"
        job["approved_at"] = datetime.now().isoformat()
        logger.info(f"Job {token} approved by admin")
        # TODO: Send SMS/email to customer confirming approval

    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.post("/admin/job/{token}/reject")
def admin_reject_job(
    token: str,
    reason: str = Form(""),
    admin_session: str | None = Cookie(None)
):
    """Reject a job"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    job = STATE.get(token)
    if job:
        job["status"] = "rejected"
        job["rejected_at"] = datetime.now().isoformat()
        job["rejection_reason"] = reason
        logger.info(f"Job {token} rejected by admin. Reason: {reason}")
        # TODO: Send SMS/email to customer with rejection reason

    return RedirectResponse(url="/admin/dashboard", status_code=303)


@app.post("/admin/job/{token}/update-price")
def admin_update_price(
    token: str,
    custom_price_low: int = Form(...),
    custom_price_high: int = Form(...),
    admin_session: str | None = Cookie(None)
):
    """Update custom pricing for a job"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    job = STATE.get(token)
    if job:
        job["custom_price_low"] = custom_price_low
        job["custom_price_high"] = custom_price_high
        logger.info(f"Job {token} price updated to £{custom_price_low}-{custom_price_high}")

    return RedirectResponse(url=f"/admin/job/{token}", status_code=303)


@app.post("/admin/job/{token}/add-note")
def admin_add_note(
    token: str,
    note: str = Form(...),
    admin_session: str | None = Cookie(None)
):
    """Add an admin note to a job"""
    if not check_admin_auth(admin_session):
        return RedirectResponse(url="/admin", status_code=303)

    job = STATE.get(token)
    if job and note.strip():
        if "admin_notes" not in job:
            job["admin_notes"] = []
        job["admin_notes"].append({
            "timestamp": datetime.now().isoformat(),
            "note": note.strip()
        })
        logger.info(f"Note added to job {token}")

    return RedirectResponse(url=f"/admin/job/{token}", status_code=303)


@app.post("/admin/job/{token}/quick-approve")
def admin_quick_approve(token: str, admin_session: str | None = Cookie(None)):
    """Quick approve from dashboard without opening details"""
    if not check_admin_auth(admin_session):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    job = STATE.get(token)
    if job:
        job["status"] = "approved"
        job["approved_at"] = datetime.now().isoformat()
        logger.info(f"Job {token} quick-approved")
        return JSONResponse({"success": True})

    return JSONResponse({"error": "Job not found"}, status_code=404)
