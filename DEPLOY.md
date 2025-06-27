# Falcon Deployment Guide

## Deploy to Render.com (Recommended - Free Tier)

### Prerequisites
1. GitHub account
2. Render.com account (free)
3. OpenRouter API key
4. Google OAuth credentials (optional)

### Step 1: Prepare Your Repository
```bash
# Commit all changes
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Select your Falcon repository
5. Render will detect the `render.yaml` file automatically
6. Click "Apply"

### Step 3: Configure Environment Variables

In Render dashboard, add these environment variables:

- `OPENROUTER_API_KEY` - Get from [openrouter.ai](https://openrouter.ai)
- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console

### Step 4: Wait for Deployment

Render will:
1. Create PostgreSQL database
2. Create Redis instance
3. Build and deploy web service
4. Run database migrations
5. Start worker process

### Your App URLs
- Web App: `https://falcon-app.onrender.com`
- API Docs: `https://falcon-app.onrender.com/docs`

---

## Alternative: Deploy to Railway.app

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Deploy
```bash
railway login
railway init
railway up
railway add postgresql
railway add redis
railway deploy
```

### Step 3: Add Environment Variables
```bash
railway variables set OPENROUTER_API_KEY=your_key
railway variables set GOOGLE_CLIENT_ID=your_id
railway variables set GOOGLE_CLIENT_SECRET=your_secret
railway deploy
```

---

## Alternative: Deploy to Heroku

### Step 1: Install Heroku CLI
```bash
# Follow instructions at https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Create App
```bash
heroku create falcon-app
heroku addons:create heroku-postgresql:mini
heroku addons:create heroku-redis:mini
```

### Step 3: Deploy
```bash
git push heroku main
heroku run alembic upgrade head
heroku ps:scale web=1 worker=1
```

### Step 4: Set Environment Variables
```bash
heroku config:set OPENROUTER_API_KEY=your_key
heroku config:set GOOGLE_CLIENT_ID=your_id
heroku config:set GOOGLE_CLIENT_SECRET=your_secret
```

---

## Post-Deployment

1. Test the application at your deployed URL
2. Configure Google OAuth redirect URI in Google Cloud Console
3. Monitor logs for any errors
4. Set up custom domain (optional)

## Important Notes

- Free tiers may have limitations (sleep after inactivity, limited resources)
- For production use, consider upgrading to paid plans
- Always use environment variables for sensitive data
- Enable HTTPS (usually automatic on these platforms)