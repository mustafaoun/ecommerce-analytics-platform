# Deploy to Heroku

Complete guide to deploy the Ecommerce Analytics Platform to Heroku.

## Prerequisites

- Heroku account (free or paid)
- Heroku CLI installed: https://devcenter.heroku.com/articles/heroku-cli
- Git repository with all code committed
- Docker installed locally (optional, for testing)

## Step 1: Create Heroku App

```bash
# Login to Heroku
heroku login

# Create a new Heroku app
heroku create your-app-name

# Or use existing app:
heroku apps:create your-app-name --region us
```

## Step 2: Add PostgreSQL Add-on

```bash
# Add PostgreSQL to your app
heroku addons:create heroku-postgresql:essential-0 --app your-app-name

# This automatically sets DATABASE_URL environment variable
# Verify it:
heroku config --app your-app-name
```

## Step 3: Set Environment Variables

```bash
# Set required environment variables
heroku config:set \
  DB_NAME=ecommerce \
  DB_USER=ecommerce_user \
  DB_PASSWORD=$(openssl rand -base64 32) \
  MB_ADMIN_EMAIL=admin@ecommerce.com \
  MB_ADMIN_PASSWORD=$(openssl rand -base64 16) \
  --app your-app-name

# Verify settings
heroku config --app your-app-name
```

## Step 4: Deploy Application

### Option A: Git Push (Recommended)

```bash
# Add Heroku remote
heroku git:remote --app your-app-name

# Push code to Heroku (triggers automatic build)
git push heroku main

# View logs
heroku logs --tail --app your-app-name
```

### Option B: Docker Image Push

```bash
# Login to Heroku Container Registry
heroku container:login

# Build and push Docker image
heroku container:push web --app your-app-name

# Release the image
heroku container:release web --app your-app-name

# View logs
heroku logs --tail --app your-app-name
```

## Step 5: Run Initialization

```bash
# Create database schema
heroku run python scripts/create_schema.py --app your-app-name

# Load sample data
heroku run python scripts/automate_etl_and_reports.py --app your-app-name

# Verify data loaded
heroku run "python -c \"from src.database.connection import get_engine; engine = get_engine(); print(engine.execute('SELECT COUNT(*) FROM users').scalar())\"" --app your-app-name
```

## Step 6: Open Application

```bash
# Open app in browser
heroku open --app your-app-name

# Or visit directly:
# https://your-app-name.herokuapp.com
```

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `DB_HOST` | localhost | PostgreSQL host |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | ecommerce | Database name |
| `DB_USER` | ecommerce_user | Database user |
| `DB_PASSWORD` | - | Database password |
| `MB_ADMIN_EMAIL` | admin@ecommerce.com | Metabase admin email |
| `MB_ADMIN_PASSWORD` | - | Metabase admin password |
| `FLASK_ENV` | production | Flask environment |

## Accessing Services

### API Dashboard
```
https://your-app-name.herokuapp.com
```

### Metabase BI Tool
```
https://your-app-name.herokuapp.com:3000
```

### API Endpoints
```
GET  https://your-app-name.herokuapp.com/api/health
GET  https://your-app-name.herokuapp.com/api/status
GET  https://your-app-name.herokuapp.com/api/analytics/revenue
POST https://your-app-name.herokuapp.com/api/etl/load-data
```

## Useful Heroku Commands

```bash
# View logs
heroku logs --tail --app your-app-name

# SSH into app
heroku ps:exec --app your-app-name

# Scale dynos
heroku ps:scale web=1 --app your-app-name

# View database
heroku pg:info --app your-app-name

# Backup database
heroku pg:backups:capture --app your-app-name

# Check app status
heroku status --app your-app-name

# Destroy app
heroku apps:destroy --app your-app-name --confirm your-app-name
```

## Troubleshooting

### App Won't Deploy
```bash
# Check build logs
heroku logs --source=app --dyno=web --app your-app-name

# Rebuild
git push heroku main --force
```

### Database Connection Issues
```bash
# Check DATABASE_URL
heroku config --app your-app-name

# Reset database
heroku pg:reset DATABASE --app your-app-name --confirm your-app-name

# Re-run initialization
heroku run python scripts/create_schema.py --app your-app-name
```

### Port Binding Error
- Ensure app listens on $PORT environment variable
- Check Procfile for correct command
- Verify Dockerfile exposes port 5000

### Memory Issues
- Scale to at least 1x dyno (512MB)
- Optimize Python dependencies
- Enable worker dyno for background jobs

## Production Checklist

- ✅ Database backed up
- ✅ Environment variables set securely
- ✅ SSL/TLS enabled (automatic on Heroku)
- ✅ Metrics monitoring configured
- ✅ Error logging set up
- ✅ Database replicated (optional)
- ✅ CDN configured (optional)

## Cost Estimation

| Service | Tier | Cost/Month |
|---------|------|-----------|
| Web Dyno | 1x (512MB) | Free or $7+ |
| PostgreSQL | Essential | Free or $50+ |
| **Total** | **Minimal** | **Free or $57+** |

## Next Steps

1. **Add Custom Domain**: `heroku domains:add yourdomain.com`
2. **Enable Automated Backups**: `heroku pg:backups:schedule`
3. **Set Up Error Tracking**: Sentry, Rollbar, or similar
4. **Monitor Performance**: Heroku Metrics dashboard
5. **Schedule Jobs**: Heroku Scheduler for periodic ETL runs

## Additional Resources

- Heroku Deployment Guide: https://devcenter.heroku.com/articles/deploying-python
- PostgreSQL on Heroku: https://devcenter.heroku.com/articles/heroku-postgresql
- Buildpacks: https://devcenter.heroku.com/articles/buildpacks
- Container Registry: https://devcenter.heroku.com/articles/container-registry-and-runtime
