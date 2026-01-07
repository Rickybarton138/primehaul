# 🚂 Deploy to Railway RIGHT NOW

## ✅ Pre-Flight Check

Your codebase is:
- ✅ Cleaned up (23 files archived)
- ✅ Committed to Git
- ✅ Production-ready
- ✅ Ready to deploy!

---

## 🚀 Railway Deployment (15 minutes)

### Step 1: Create GitHub Repo (5 min)

**Option A: Via GitHub Website**
1. Go to: https://github.com/new
2. Repository name: `primehaul-os`
3. Make it **Private** (important!)
4. Click "Create repository"
5. **Don't** initialize with README (we already have one)

**Option B: Via GitHub CLI** (if you have it)
```bash
gh repo create primehaul-os --private --source=. --remote=origin --push
```

---

### Step 2: Push Code to GitHub (2 min)

After creating the repo, GitHub shows you commands. Run:

```bash
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/primehaul-os.git

# Push code
git branch -M main
git push -u origin main
```

**Verify**: Visit your GitHub repo - you should see all files!

---

### Step 3: Sign Up for Railway (2 min)

1. Go to: https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway app
4. ✅ You get $5 free credit!

---

### Step 4: Create New Project (1 min)

1. Click "New Project"
2. Choose "Deploy from GitHub repo"
3. Select your `primehaul-os` repo
4. Railway auto-detects Python and starts deploying!

**Wait 1-2 minutes** - Railway will build your app

---

### Step 5: Add PostgreSQL Database (30 seconds)

1. In your Railway project, click "New"
2. Choose "Database" → "PostgreSQL"
3. ✅ Done! Railway automatically creates `DATABASE_URL` variable

---

### Step 6: Configure Environment Variables (3 min)

Click your app service → "Variables" tab → Add these:

#### **Required Variables:**

```bash
# OpenAI (for AI photo analysis)
OPENAI_API_KEY=sk-proj-your-key-here

# Mapbox (for address autocomplete)
MAPBOX_ACCESS_TOKEN=pk.your-mapbox-token-here

# Secret Key (generate with command below)
SECRET_KEY=your-64-character-random-string-here

# Staging Mode (password protect site)
STAGING_MODE=true
STAGING_USERNAME=primehaul
STAGING_PASSWORD=ChooseYourSecurePassword123
```

#### **Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### **Optional Variables:**

```bash
# Twilio SMS (optional)
TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+447123456789

# Stripe Billing (optional)
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
```

**Click "Add"** after each variable.

---

### Step 7: Verify Deployment (1 min)

1. Railway shows deployment status
2. Wait for "Success" ✅
3. Click "View Logs" to see:
   ```
   Running migrations...
   Starting server...
   Uvicorn running on http://0.0.0.0:XXXX
   ```

4. Click "Deployments" → Your app URL (like `primehaul-os-production.up.railway.app`)
5. Visit it - you should see password prompt! 🔒

---

### Step 8: Connect Your Domain (3 min)

#### **In Railway:**
1. Click your service
2. "Settings" → "Networking"
3. Click "Custom Domain"
4. Enter: `staging.primehaul.co.uk`
5. Railway shows you a CNAME target (like `abc123.railway.app`)

#### **In Your Domain Registrar** (Namecheap, GoDaddy, etc.):

1. Login to your domain dashboard
2. Find DNS Management for `primehaul.co.uk`
3. Add **CNAME Record**:
   - **Type**: CNAME
   - **Host**: staging
   - **Target**: `abc123.railway.app` (from Railway)
   - **TTL**: 3600 (or Auto)
4. Save

**Wait 5-60 minutes** for DNS to propagate.

**Check DNS**: https://whatsmydns.net/?s=staging.primehaul.co.uk

---

### Step 9: Test Your Staging Site! (2 min)

Once DNS propagates, visit: `https://staging.primehaul.co.uk`

**You should see**:
- 🔒 Browser password prompt
- Enter username: `primehaul`
- Enter password: (whatever you set)
- ✅ Beautiful landing page loads!

**Test these pages**:
- Landing: https://staging.primehaul.co.uk/
- Terms: https://staging.primehaul.co.uk/terms
- Privacy: https://staging.primehaul.co.uk/privacy
- Contact: https://staging.primehaul.co.uk/contact
- Signup: https://staging.primehaul.co.uk/auth/signup

---

### Step 10: Create Test Account (2 min)

1. Go to: https://staging.primehaul.co.uk/auth/signup
2. Fill in company details
3. Create account
4. Login at: https://staging.primehaul.co.uk/auth/login
5. ✅ You're in the admin dashboard!

**Test the customer flow**:
1. Click "New Quote" or go to: https://staging.primehaul.co.uk/s/YOUR_COMPANY_SLUG/test123/start-v2
2. Fill in addresses
3. Upload photos
4. See AI analysis work
5. Get instant quote!

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Railway deployment succeeded
- [ ] PostgreSQL database connected
- [ ] App accessible at Railway URL
- [ ] Password protection works (STAGING_MODE=true)
- [ ] Custom domain connected (staging.primehaul.co.uk)
- [ ] SSL certificate active (https://)
- [ ] Landing page loads
- [ ] Can create account
- [ ] Can login to admin
- [ ] Customer flow works (addresses, photos, AI)
- [ ] Mobile responsive (test on phone)

---

## 🎉 You're Live!

Your staging site is now at: **https://staging.primehaul.co.uk** 🔒

**Share with friends**:
- URL: https://staging.primehaul.co.uk
- Username: primehaul
- Password: (your password)

---

## 🐛 Troubleshooting

### Deployment Failed
```bash
# Check Railway logs
Click "Deployments" → View Logs
# Look for error messages
```

### Database Connection Error
```bash
# Verify DATABASE_URL is set automatically
Click "Variables" tab → Should see DATABASE_URL
```

### Password Not Working
```bash
# Check environment variables
STAGING_MODE=true  (not "True")
STAGING_USERNAME=primehaul
STAGING_PASSWORD=YourPassword
```

### DNS Not Working
```bash
# Check DNS propagation
https://whatsmydns.net/?s=staging.primehaul.co.uk

# Wait 24 hours if needed
# Clear browser cache
```

### AI Not Working
```bash
# Check OpenAI API key
Click "Variables" → OPENAI_API_KEY
# Verify OpenAI account has credits
```

---

## 💰 Costs

**Railway**:
- Month 1: Free ($5 credit covers basic usage)
- Month 2+: ~$5-20/month (usage-based)

**If you run out of free credit**:
- Add payment method in Railway settings
- $5/month minimum covers most usage

---

## 🚀 Going Public (When Ready)

To make the site public (no password):

1. **In Railway** → Variables:
   ```bash
   STAGING_MODE=false
   ```
2. **Save** (auto-redeploys)
3. **Point main domain**:
   - Add another custom domain: `primehaul.co.uk`
   - Update DNS: `@` → Railway CNAME
4. **Launch!** Site is public at https://primehaul.co.uk

---

## 📞 Need Help?

**Railway Logs**:
```bash
# In Railway dashboard
Click your service → "Deployments" → Latest deployment → "View Logs"
```

**Railway Status**:
https://status.railway.app

**Railway Docs**:
https://docs.railway.app

---

## 🎯 Next Steps

1. ✅ Deploy to Railway (you're doing this now!)
2. Test thoroughly on staging
3. Show 5-10 friends for feedback
4. Fix any issues
5. Flip `STAGING_MODE=false`
6. Point main domain
7. Launch publicly! 🎉

---

**Time to Complete**: ~15 minutes
**Difficulty**: Easy
**Result**: Production staging site with SSL! 🚀

Let's go! 💪
