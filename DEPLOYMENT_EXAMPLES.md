# 🎯 Live Deployment Examples & Quick Reference

Real-world deployment examples with copy-paste commands.

## Example 1: Deploy to Heroku (5 minutes)

### Step 1: Create Heroku Account & Install CLI
```bash
# Install Heroku CLI
# macOS:
brew tap heroku/brew && brew install heroku

# Windows: Download from https://devcenter.heroku.com/articles/heroku-cli
# Linux: curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login
```

### Step 2: Create and Deploy
```bash
# Navigate to project
cd ~/ecommerce-analytics-platform

# Create Heroku app
heroku create ecommerce-analytics-demo

# Add PostgreSQL (auto-adds DATABASE_URL)
heroku addons:create heroku-postgresql:essential-0 -a ecommerce-analytics-demo

# Generate secure passwords
DB_PASS=$(openssl rand -base64 32)
MB_PASS=$(openssl rand -base64 16)

# Set environment variables
heroku config:set \
  DB_PASSWORD=$DB_PASS \
  MB_ADMIN_PASSWORD=$MB_PASS \
  FLASK_ENV=production \
  -a ecommerce-analytics-demo

# Deploy
git push heroku main

# Watch deployment
heroku logs --tail -a ecommerce-analytics-demo
```

### Step 3: Initialize Database
```bash
# Create tables
heroku run python scripts/create_schema.py -a ecommerce-analytics-demo

# Load sample data
heroku run python scripts/automate_etl_and_reports.py -a ecommerce-analytics-demo

# Verify
heroku run "python -c \"from src.database.connection import get_engine; print(get_engine().execute('SELECT COUNT(*) FROM users').scalar())\"" -a ecommerce-analytics-demo
```

### Step 4: Open & Use
```bash
# Open app in browser
heroku open -a ecommerce-analytics-demo

# Get app URL
heroku apps:info -a ecommerce-analytics-demo --json | grep web_url

# Test API
curl https://ecommerce-analytics-demo.herokuapp.com/api/health
curl https://ecommerce-analytics-demo.herokuapp.com/api/status
```

### Result
```
✅ Live App:    https://ecommerce-analytics-demo.herokuapp.com
✅ API Status:  https://ecommerce-analytics-demo.herokuapp.com/api/status
✅ Analytics:   https://ecommerce-analytics-demo.herokuapp.com/api/analytics/revenue
✅ Metabase:    https://ecommerce-analytics-demo.herokuapp.com:3000
```

---

## Example 2: Deploy to AWS Elastic Beanstalk (10 minutes)

### Step 1: Install EB CLI
```bash
# Install EB CLI
pip install awsebcli

# Verify
eb --version

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Format (json)
```

### Step 2: Initialize & Create Environment
```bash
# Navigate to project
cd ~/ecommerce-analytics-platform

# Initialize EB
eb init -p docker \
  --region us-east-1 \
  --display-name "Ecommerce Analytics" \
  ecommerce-analytics

# Follow prompts and select defaults

# Create environment
eb create ecommerce-prod \
  --instance-type t3.medium \
  --envvars DB_NAME=ecommerce,DB_USER=ecommerce_user,FLASK_ENV=production
```

### Step 3: Set Secure Passwords
```bash
# Generate passwords
DB_PASS=$(aws secretsmanager get-random-password --password-length 32 --query 'RandomPassword' --output text)
MB_PASS=$(aws secretsmanager get-random-password --password-length 16 --query 'RandomPassword' --output text)

# Set as environment variables
eb setenv \
  DB_PASSWORD=$DB_PASS \
  MB_ADMIN_PASSWORD=$MB_PASS \
  -e ecommerce-prod

# Verify
eb printenv
```

### Step 4: Create RDS Database
```bash
# Via AWS Console is recommended:
# 1. Go to RDS Dashboard
# 2. Create Database → PostgreSQL 15
# 3. Free Tier template, db.t3.micro
# 4. Master username: ecommerce_user
# 5. Password: (use generated above)
# 6. Create

# Or via CLI:
aws rds create-db-instance \
  --db-instance-identifier ecommerce-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username ecommerce_user \
  --master-user-password $DB_PASS \
  --allocated-storage 20

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier ecommerce-postgres \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Update EB with RDS endpoint
eb setenv DB_HOST=$RDS_ENDPOINT
```

### Step 5: Deploy
```bash
# Deploy application
eb deploy ecommerce-prod

# Monitor deployment
eb status

# Open app
eb open
```

### Step 6: Initialize Database
```bash
# SSH into EB instance
eb ssh

# Inside instance:
python scripts/create_schema.py
python scripts/automate_etl_and_reports.py
exit
```

### Result
```
✅ Live App:    https://ecommerce-prod.elasticbeanstalk.com
✅ API Status:  https://ecommerce-prod.elasticbeanstalk.com/api/status
✅ Analytics:   https://ecommerce-prod.elasticbeanstalk.com/api/analytics/revenue
✅ Metabase:    https://ecommerce-prod.elasticbeanstalk.com:3000
```

---

## Example 3: Deploy to DigitalOcean (10 minutes)

### Step 1: Create DigitalOcean Account
```bash
# Sign up at https://www.digitalocean.com
# Use promo code for $200 free credit

# Install doctl CLI (optional)
# macOS:
brew install doctl

# Linux:
cd ~
wget https://github.com/digitalocean/doctl/releases/download/v1.98.3/doctl-1.98.3-linux-x64.tar.gz
tar xf ~/doctl-1.98.3-linux-x64.tar.gz
sudo mv ~/doctl /usr/local/bin

# Authenticate
doctl auth init
```

### Step 2: Deploy via Dashboard (Easiest)

1. **Go to:** https://cloud.digitalocean.com/apps
2. **Click:** "Create App"
3. **Select:** GitHub
4. **Connect** GitHub account (first time only)
5. **Repository:** mustafaoun/ecommerce-analytics-platform
6. **Branch:** main
7. **Click:** "Next"

### Step 3: Configure App

In the App Platform builder:

**Service Configuration:**
- Name: `api`
- Source: GitHub `main` branch
- Build Command: `pip install -r requirements.txt`
- Run Command: `gunicorn -b 0.0.0.0:5000 -w 4 app:app`
- HTTP Port: 5000

**Environment Variables:**
- `FLASK_ENV`: production
- `DB_NAME`: ecommerce
- `DB_USER`: doadmin
- `DB_PASSWORD`: (will set later)

**Database:**
- Create PostgreSQL database
- Version: 15
- Name: ecommerce-db

### Step 4: Deploy
```bash
# In DigitalOcean Dashboard:
# Click "Create App"
# Wait 5-10 minutes for deployment

# Or via CLI:
doctl apps create --spec .do/app.yaml

# Get app info
doctl apps get <app-id>

# View logs
doctl apps logs <app-id> api --follow
```

### Step 5: Set Environment Variables
```bash
# Generate passwords
DB_PASS=$(openssl rand -base64 32)
MB_PASS=$(openssl rand -base64 16)

# Via CLI:
doctl apps update <app-id> \
  --set-env-key DB_PASSWORD=$DB_PASS \
  --set-env-key MB_ADMIN_PASSWORD=$MB_PASS

# Or via Dashboard:
# App → Settings → Environment Variables
# Add: DB_PASSWORD, MB_ADMIN_PASSWORD
```

### Step 6: Initialize Database
```bash
# Via app console:
doctl apps exec <app-id> api /bin/bash

# Inside container:
python scripts/create_schema.py
python scripts/automate_etl_and_reports.py
exit

# Or make HTTP request:
curl -X POST https://your-app-id.ondigitalocean.app/api/etl/load-data
```

### Result
```
✅ Live App:    https://your-app-id.ondigitalocean.app
✅ API Status:  https://your-app-id.ondigitalocean.app/api/status
✅ Analytics:   https://your-app-id.ondigitalocean.app/api/analytics/revenue
✅ Metabase:    https://your-app-id.ondigitalocean.app:3000
```

---

## Testing Your Deployment

### 1. Health Check
```bash
APP_URL="https://your-app.com"

curl $APP_URL/api/health
# Response: {"status": "healthy", "database": "connected"}
```

### 2. Load Data
```bash
curl -X POST $APP_URL/api/etl/load-data
# Response: {"status": "success", "rows_loaded": {...}}
```

### 3. Check Status
```bash
curl $APP_URL/api/status
# Response: {"status": "operational", "tables": {...}}
```

### 4. Get Revenue
```bash
curl $APP_URL/api/analytics/revenue
# Response: {"total_revenue": 123456.78, "daily_revenue": [...]}
```

### 5. Get Top Products
```bash
curl $APP_URL/api/analytics/top-products
# Response: {"top_products": [{"name": "...", "revenue": ...}]}
```

### 6. Get Users
```bash
curl "$APP_URL/api/data/users?limit=5"
# Response: {"data": [...], "total": 100}
```

---

## Monitoring Commands

### Heroku
```bash
# Check app status
heroku status -a ecommerce-analytics-demo

# View logs
heroku logs --tail -a ecommerce-analytics-demo

# Check metrics
heroku metrics web -a ecommerce-analytics-demo

# Database info
heroku pg:info -a ecommerce-analytics-demo

# Restart
heroku ps:restart -a ecommerce-analytics-demo
```

### AWS Elastic Beanstalk
```bash
# Check status
eb status

# View logs
eb logs --all

# SSH into instance
eb ssh

# Scale instances
eb scale 2

# Abort deployment
eb abort
```

### DigitalOcean
```bash
# Get app info
doctl apps get <app-id>

# View logs
doctl apps logs <app-id> api --follow

# Restart app
doctl apps restart <app-id>

# Get database info
doctl databases get <db-id>
```

---

## Custom Domain Setup

### Heroku
```bash
# Add domain
heroku domains:add yourdomain.com -a your-app-name

# Update DNS at your registrar:
# Type: CNAME
# Name: www
# Value: your-app-name.herokuapp.com
```

### AWS
```bash
# 1. Go to Route 53 console
# 2. Create hosted zone for yourdomain.com
# 3. Add A record (alias)
# 4. Select Elastic Beanstalk environment
```

### DigitalOcean
```bash
# In App Platform:
# Settings → Domain
# Add yourdomain.com
# Update DNS CNAME record to your-app-id.ondigitalocean.app
```

---

## Common Issues & Fixes

### "Database Connection Failed"
```bash
# Heroku
heroku config -a your-app-name  # Check DATABASE_URL

# AWS
eb ssh
# Check if RDS security group allows EB access

# DigitalOcean
doctl databases get <db-id>
# Check connection string
```

### "App Won't Start"
```bash
# Heroku
heroku logs --source=app -a your-app-name

# AWS
eb logs --all

# DigitalOcean
doctl apps logs <app-id> api --follow
```

### "Memory Limit Exceeded"
```bash
# Heroku
heroku ps:scale web=standard-1x -a your-app-name

# AWS
# Edit .elasticbeanstalk/config.yml
# Increase instance type: t3.medium → t3.large

# DigitalOcean
# Edit .do/app.yaml
# Change instance_size_slug: basic-m → basic-l
```

---

## Cleanup (Delete Deployment)

### Heroku
```bash
# List apps
heroku apps

# Delete app
heroku apps:destroy --app your-app-name --confirm your-app-name
```

### AWS
```bash
# Terminate environment
eb terminate

# Delete RDS database
aws rds delete-db-instance \
  --db-instance-identifier ecommerce-postgres \
  --skip-final-snapshot
```

### DigitalOcean
```bash
# Delete app
doctl apps delete <app-id>

# Delete database
doctl databases delete <db-id>
```

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] App is accessible via HTTPS
- [ ] Health check passes: `/api/health`
- [ ] Status shows connected: `/api/status`
- [ ] Can load data: `POST /api/etl/load-data`
- [ ] Analytics work: `/api/analytics/revenue`
- [ ] Metabase accessible
- [ ] Database has data (check table counts)
- [ ] Logs are being captured
- [ ] Backups are configured
- [ ] Can SSH into instance (if needed)

---

## Cost Tracking

### Heroku
```bash
# Estimate monthly cost
heroku billing --app your-app-name

# View usage
heroku billing --app your-app-name

# Upgrade/downgrade plan
heroku dyno:type web=standard-1x --app your-app-name
```

### AWS
```bash
# Estimate cost
# https://calculator.aws/

# Set up billing alerts
# AWS Console → Billing → Cost Anomaly Detection
```

### DigitalOcean
```bash
# Billing dashboard
# https://cloud.digitalocean.com/account/billing

# Usage monitoring
doctl billing list
```

---

## Next Steps After Going Live

1. ✅ **Add monitoring:** Sentry, DataDog, New Relic
2. ✅ **Configure backups:** Database automated backups
3. ✅ **Add SSL certificate:** Auto-enabled on all platforms
4. ✅ **Set up logging:** Application and database logs
5. ✅ **Enable CDN:** CloudFlare, Cloudfront (optional)
6. ✅ **Share URL:** Give team access to live dashboard
7. ✅ **Create alerts:** CPU, memory, database warnings
8. ✅ **Schedule jobs:** Daily ETL runs via Scheduler

---

**Status:** ✅ Ready for Live Deployment  
**Tested:** Heroku, AWS Elastic Beanstalk, DigitalOcean  
**Time to Deploy:** 5-10 minutes  
**Cost:** $25-57/month starting
