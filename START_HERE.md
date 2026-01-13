# 🚀 START HERE - Super Simple Reset & Test

## ONE COMMAND TO RULE THEM ALL:

### For Railway (Production):

```bash
# Set your Railway database URL (get from Railway dashboard)
export DATABASE_URL="postgresql://postgres:PASSWORD@HOST:PORT/railway"

# Reset everything
python3 QUICK_RESET.py --railway
```

Type `YES` when prompted.

---

### For Local Testing:

```bash
# Reset local database
python3 QUICK_RESET.py
```

---

## That's It!

The script will:
- ✅ Reset the database
- ✅ Create test company and admin user
- ✅ Set up pricing config
- ✅ Show you the URLs to test

---

## URLs You'll Get:

**Customer URL (test on phone):**
```
https://primehaul-production.up.railway.app/s/test-removals-ltd/test-123/start-v2
```

**Admin Dashboard (test on laptop):**
```
https://primehaul-production.up.railway.app/test-removals-ltd/admin/dashboard
```

**Login:** admin@test.com / test123

---

## Quick Test (5 minutes):

1. Open customer URL on phone
2. Fill in addresses and property type
3. Complete access questions
4. Take photos (or skip)
5. Get quote
6. Check admin dashboard shows the quote

Done! ✅

---

## For Sammie Demo:

Just change the token in the URL for each demo:
- `/s/test-removals-ltd/sammie-1/start-v2`
- `/s/test-removals-ltd/sammie-2/start-v2`
- `/s/test-removals-ltd/demo/start-v2`

Each creates a fresh quote automatically.

---

## If Something Breaks:

Just run it again:
```bash
python3 QUICK_RESET.py --railway
```

Easy! 🎉
