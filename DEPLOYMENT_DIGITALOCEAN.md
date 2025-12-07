# Deploy to DigitalOcean App Platform

Complete guide to deploy the Ecommerce Analytics Platform to DigitalOcean App Platform.

## Prerequisites

- DigitalOcean account (free $200 credit for new users)
- GitHub repository with code
- DigitalOcean CLI (doctl): https://docs.digitalocean.com/reference/doctl/
- or use DigitalOcean Dashboard (no CLI needed)

## Step 1: Create DigitalOcean App (Via Dashboard)

### Option A: Dashboard (Easiest)

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Select "GitHub" repository source
4. Connect GitHub account (first time only)
5. Select `ecommerce-analytics-platform` repository
6. Choose branch: `main`
7. Click "Next"

### Option B: App Spec (YAML Configuration)

Create `.do/app.yaml`:

```yaml
name: ecommerce-analytics-platform
services:
  - name: api
    github:
      repo: mustafaoun/ecommerce-analytics-platform
      branch: main
    build_command: pip install -r requirements.txt
    http_port: 5000
    envs:
      - key: FLASK_ENV
        value: production
      - key: DB_HOST
        scope: RUN_TIME
      - key: DB_PORT
        value: "5432"
      - key: DB_NAME
        value: ecommerce
      - key: DB_USER
        scope: RUN_TIME
      - key: DB_PASSWORD
        scope: RUN_TIME
        value: ${db.password}
    health_check:
      http_path: /api/health

databases:
  - name: ecommerce-db
    engine: PG
    version: "15"
    production: true
```

## Step 2: Configure Database

### Via Dashboard:

1. In App Platform, click "Create resource"
2. Select "Database"
3. Choose:
   - Engine: PostgreSQL
   - Version: 15
   - Production: Yes
   - Name: ecommerce-db

### Via CLI:

```bash
# Create database cluster
doctl databases create \
  --engine pg \
  --version 15 \
  --region nyc3 \
  --num-nodes 1 \
  ecommerce-db

# Get connection string
doctl databases connection get ecommerce-db
```

## Step 3: Set Environment Variables

### Via Dashboard:

1. Go to App Settings → "App-level environment variables"
2. Add variables:
   - `DB_HOST`: Database hostname (auto-populated)
   - `DB_PORT`: 5432
   - `DB_NAME`: ecommerce
   - `DB_USER`: doadmin
   - `DB_PASSWORD`: (from database credentials)
   - `MB_ADMIN_EMAIL`: admin@ecommerce.com
   - `MB_ADMIN_PASSWORD`: (generate secure password)
   - `FLASK_ENV`: production

### Via CLI:

```bash
doctl apps create --spec .do/app.yaml
```

## Step 4: Configure Service Settings

### HTTP Health Check

1. Go to Component Settings → "Health check"
2. Path: `/api/health`
3. HTTP port: 5000
4. Initial delay: 10s
5. Period: 10s

### HTTP Routes

1. Click "Routes"
2. Add route:
   - Source: `/`
   - Destination: `api`
   - Protocol: HTTP

## Step 5: Deploy Application

### Via Dashboard:

1. Click "Create App"
2. Review configuration
3. Click "Deploy"
4. Monitor deployment progress

### Via CLI:

```bash
# Deploy from spec file
doctl apps create --spec .do/app.yaml

# Monitor deployment
doctl apps get-deployment <app-id>

# View logs
doctl apps logs <app-id> api
```

## Step 6: Initialize Database

```bash
# Get App URL
APP_URL=$(doctl apps get <app-id> --format live-url --no-header)

# Create schema
curl -X POST $APP_URL/api/etl/generate-data \
  -H "Content-Type: application/json" \
  -d '{"n_users": 100, "n_products": 50}'

# Load sample data
curl -X POST $APP_URL/api/etl/load-data
```

Or use App Console:

```bash
# SSH into running container
doctl apps exec <app-id> api /bin/bash

# Run commands
python scripts/create_schema.py
python scripts/automate_etl_and_reports.py
```

## Step 7: Access Your Application

```
Frontend: https://your-app-id-xyz.ondigitalocean.app
API:      https://your-app-id-xyz.ondigitalocean.app/api
Metabase: https://your-app-id-xyz.ondigitalocean.app:3000
```

## Step 8: Add Custom Domain (Optional)

1. Go to App Settings → "Domain"
2. Click "Add domain"
3. Enter your domain: `yourdomain.com`
4. Update DNS records at your registrar:
   - Type: CNAME
   - Name: @
   - Value: your-app-id-xyz.ondigitalocean.app
5. Wait for DNS propagation (5-30 minutes)

## .do/app.yaml - Complete Configuration

```yaml
name: ecommerce-analytics-platform
services:
  - name: api
    github:
      repo: mustafaoun/ecommerce-analytics-platform
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: gunicorn -b 0.0.0.0:5000 -w 4 --timeout 120 app:app
    http_port: 5000
    instance_count: 1
    instance_size_slug: basic-s
    source_dir: /
    
    health_check:
      http_path: /api/health
      initial_delay_seconds: 10
      period_seconds: 10
      timeout_seconds: 5
      success_threshold: 1
      failure_threshold: 5
    
    log_destinations:
      - name: logs
        papertrail:
          token: ${log_token}
    
    envs:
      - key: FLASK_ENV
        value: production
      - key: DB_HOST
        value: ${db.hostname}
      - key: DB_PORT
        value: ${db.port}
      - key: DB_NAME
        value: ecommerce
      - key: DB_USER
        value: ${db.username}
      - key: DB_PASSWORD
        value: ${db.password}
      - key: MB_ADMIN_EMAIL
        value: admin@ecommerce.com
      - key: MB_ADMIN_PASSWORD
        scope: RUN_TIME

static_sites:
  - name: docs
    source_dir: ./docs
    routes:
      - path: /docs

databases:
  - name: db
    engine: PG
    version: "15"
    production: true
    
jobs:
  - name: init-db
    kind: PRE_DEPLOY
    github:
      repo: mustafaoun/ecommerce-analytics-platform
      branch: main
    build_command: pip install -r requirements.txt
    run_command: python scripts/create_schema.py
    environment_slug: basic-xs
```

## Useful DigitalOcean Commands

```bash
# List apps
doctl apps list

# Get app details
doctl apps get <app-id>

# View logs
doctl apps logs <app-id> api

# View deployment logs
doctl apps logs <app-id> api --follow

# Execute command in app
doctl apps exec <app-id> api /bin/bash

# Update app spec
doctl apps update <app-id> --spec .do/app.yaml

# Delete app
doctl apps delete <app-id>

# Get database info
doctl databases get <db-id>

# Create database backup
doctl databases backup create <db-id>
```

## Environment Variables Reference

| Variable | Source | Purpose |
|----------|--------|---------|
| `DB_HOST` | Database | PostgreSQL hostname |
| `DB_PORT` | Database | PostgreSQL port (5432) |
| `DB_NAME` | Manual | Database name (ecommerce) |
| `DB_USER` | Database | Database user (doadmin) |
| `DB_PASSWORD` | Database | Database password |
| `MB_ADMIN_EMAIL` | Manual | Metabase admin email |
| `MB_ADMIN_PASSWORD` | Manual | Metabase admin password |
| `FLASK_ENV` | Manual | Flask environment (production) |

## Scaling Configuration

```yaml
# In .do/app.yaml
services:
  - name: api
    instance_count: 2          # Number of instances
    instance_size_slug: basic-m # Instance size
    http_port: 5000
    
    # Auto-scaling (with starter tier or higher)
    autoscaling:
      max_instance_count: 5
      metrics:
        cpu:
          percent: 70
        memory_percent: 80
```

## Log Management

```bash
# Stream logs
doctl apps logs <app-id> api --follow

# Export logs
doctl apps logs <app-id> api > app_logs.txt

# Get specific time range logs
doctl apps logs <app-id> api --since 1h
```

## Monitoring & Alerts

### Via Dashboard:

1. Click App → "Insights"
2. View metrics:
   - CPU usage
   - Memory usage
   - Request count
   - Error rate
   - Response time

### Via CLI:

```bash
doctl monitoring create-alert \
  --description "High CPU" \
  --enabled true \
  --compare GREATER_THAN \
  --value 80 \
  --window 5m
```

## Production Checklist

- ✅ Database version: PostgreSQL 15
- ✅ Production database: Yes
- ✅ Database backups: Automated daily
- ✅ SSL/TLS: Auto-enabled
- ✅ Health checks: Configured
- ✅ Environment variables: Secured
- ✅ Auto-deploy on push: Enabled
- ✅ Instance count: ≥2 for HA
- ✅ Monitoring: Enabled
- ✅ Custom domain: Configured

## Cost Estimation

| Service | Tier | Cost/Month |
|---------|------|-----------|
| App (basic-s) | 1 instance | $6 |
| Database (PostgreSQL) | 1GB RAM | $15 |
| Bandwidth | Standard | $0-5 |
| **Total** | **Minimal** | **~$21-26** |

## Troubleshooting

### Deployment Failed
```bash
# View deployment logs
doctl apps logs <app-id> api --follow

# Redeploy
doctl apps propose <app-id> --spec .do/app.yaml
doctl apps update <app-id> --spec .do/app.yaml
```

### Database Connection Error
```bash
# Check database status
doctl databases get <db-id>

# Verify credentials
doctl databases user list <db-id>

# Check firewall rules
doctl databases firewall list <db-id>
```

### App Not Responding
```bash
# Restart app
doctl apps restart <app-id>

# Check app status
doctl apps get <app-id> --format status
```

## GitHub Integration

The App Platform automatically:
- Watches GitHub repository for changes
- Rebuilds on push to `main` branch
- Deploys automatically
- Generates preview deploys for PRs (optional)

To disable auto-deploy:
1. Go to App Settings → "Build & Deploy"
2. Toggle "Deploy on push": Off

## Disaster Recovery

```bash
# Create manual backup
doctl databases backup create <db-id>

# List backups
doctl databases backup list <db-id>

# Restore from backup
doctl databases backup restore <db-id> <backup-id>
```

## Additional Resources

- DigitalOcean App Platform: https://docs.digitalocean.com/products/app-platform/
- PostgreSQL on DigitalOcean: https://docs.digitalocean.com/products/databases/postgresql/
- Pricing: https://www.digitalocean.com/pricing/app-platform
- Support: https://www.digitalocean.com/support/
