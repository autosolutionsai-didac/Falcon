# Auto-Deploy Setup

## Current Workflow ✅

When you make changes locally and push to GitHub, Render will automatically:
1. Detect the push to `main` branch
2. Rebuild your app
3. Deploy the new version
4. Zero downtime deployment

## Steps to Enable Auto-Deploy

### 1. Initialize Git (if not done)
```bash
cd /home/didacfg/my-projects-claude-code/Falcon/Falcon
git init
git add .
git commit -m "Initial commit"
```

### 2. Create GitHub Repository
```bash
# Create repo on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/Falcon.git
git branch -M main
git push -u origin main
```

### 3. Connect to Render
1. Go to render.com
2. New > Blueprint
3. Connect GitHub account
4. Select your Falcon repository
5. Render auto-detects `render.yaml`
6. Click "Apply"

### 4. Every Time You Make Changes
```bash
# Make your changes locally
# Test locally first
uvicorn app.main:app --reload

# When ready, push to GitHub
git add .
git commit -m "Add new feature"
git push

# Render automatically deploys! (takes ~3-5 minutes)
```

## Watch Deployment Progress
1. Go to Render dashboard
2. Click on your service
3. View "Logs" tab
4. Watch real-time deployment

## Deployment Notifications
In Render settings, enable:
- Email notifications on deploy success/failure
- Slack/Discord webhooks (optional)

## Rollback if Needed
```bash
# If something breaks, rollback in Render dashboard
# Or use git:
git revert HEAD
git push
```

## Pro Tips
- Always test locally first
- Use feature branches for big changes
- Set up staging environment for testing
- Monitor logs after deployment