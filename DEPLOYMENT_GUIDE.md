# Live Deployment Guide - Ecommerce Analytics Platform

Choose your hosting platform and follow the detailed deployment guide.

## Quick Platform Comparison

| Platform | Ease | Cost | Scalability | Best For |
|----------|------|------|-------------|----------|
| **Heroku** | ⭐⭐⭐⭐⭐ | ~$57/mo | Good | Quick prototyping |
| **AWS EB** | ⭐⭐⭐ | ~$50/mo | Excellent | Enterprise apps |
| **DigitalOcean** | ⭐⭐⭐⭐ | ~$25/mo | Good | Cost-effective |

## 1. Deploy to Heroku (Recommended for Quick Start)

### In 5 Minutes:

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Set environment variables
heroku config:set \
  DB_PASSWORD=$(openssl rand -base64 32) \
  MB_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Deploy
git push heroku main

# Initialize database
heroku run python scripts/create_schema.py

# Open app
heroku open
```

**Full Guide:** See `DEPLOYMENT_HEROKU.md`

**Live Demo URL:** `https://your-app-name.herokuapp.com`

---

## 2. Deploy to AWS Elastic Beanstalk

### For Enterprise Scale:

```bash
# Initialize EB
eb init -p docker ecommerce-analytics --region us-east-1

# Create environment
eb create ecommerce-prod --instance-type t3.medium --scale 1

# Set environment variables
eb setenv DB_PASSWORD=... MB_ADMIN_PASSWORD=...

# Deploy
eb deploy

# Initialize database
eb ssh
python scripts/create_schema.py
exit
```

**Full Guide:** See `DEPLOYMENT_AWS.md`

**Live Demo URL:** `https://ecommerce-prod.elasticbeanstalk.com`

---

## 3. Deploy to DigitalOcean App Platform

### Most Affordable:

```bash
# Via Dashboard:
# 1. Go to cloud.digitalocean.com/apps
# 2. Click "Create App"
# 3. Connect GitHub
# 4. Select repository and branch
# 5. Add PostgreSQL database
# 6. Deploy

# Via CLI:
doctl apps create --spec .do/app.yaml

# View logs
doctl apps logs <app-id> api --follow

# Access app
https://your-app-id.ondigitalocean.app
```

**Full Guide:** See `DEPLOYMENT_DIGITALOCEAN.md`

**Live Demo URL:** `https://your-app-id.ondigitalocean.app`

---

## Deployment Checklist

### Before Deployment

- ✅ All code committed to GitHub
- ✅ Environment variables configured
- ✅ Dockerfile builds locally: `docker build -t test .`
- ✅ Database schema tested: `python scripts/create_schema.py`
- ✅ ETL pipeline tested: `python scripts/run_etl.py`
- ✅ Requirements.txt up to date

### After Deployment

- ✅ Health check passes: `curl https://app.example.com/api/health`
- ✅ Database connected: `curl https://app.example.com/api/status`
- ✅ Can load data: `curl -X POST https://app.example.com/api/etl/load-data`
- ✅ Metabase accessible: `https://app.example.com:3000`
- ✅ Reports generate: `curl https://app.example.com/api/analytics/revenue`

---

## API Endpoints (Post-Deployment)

### Health & Status
```bash
# Health check
curl https://your-app.example.com/api/health

# Platform status
curl https://your-app.example.com/api/status
```

### Data Access
```bash
# Get users (paginated)
curl https://your-app.example.com/api/data/users?limit=10&offset=0

# Get orders
curl https://your-app.example.com/api/data/orders?limit=10
```

### Analytics
```bash
# Revenue metrics
curl https://your-app.example.com/api/analytics/revenue

# Top products
curl https://your-app.example.com/api/analytics/top-products

# Customer KPIs
curl https://your-app.example.com/api/analytics/customer-metrics
```

### ETL Operations
```bash
# Generate data
curl -X POST https://your-app.example.com/api/etl/generate-data \
  -H "Content-Type: application/json" \
  -d '{"n_users": 100, "n_products": 50}'

# Load data
curl -X POST https://your-app.example.com/api/etl/load-data
```

---

## Environment Variables

Required variables for all platforms:

```env
# Database
DB_HOST=<db-host>
DB_PORT=5432
DB_NAME=ecommerce
DB_USER=<db-user>
DB_PASSWORD=<secure-password>

# Metabase
MB_ADMIN_EMAIL=admin@ecommerce.com
MB_ADMIN_PASSWORD=<secure-password>

# Flask
FLASK_ENV=production
```

Generate secure passwords:
```bash
# Random 32-char password
openssl rand -base64 32

# Random 16-char password
openssl rand -base64 16
```

---

## Service Architecture

```
┌──────────────────────────────────────────┐
│         Your Domain (HTTPS)              │
│      https://your-app.example.com        │
└──────────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    ┌───▼───┐           ┌────▼─────┐
    │ Flask │           │ Metabase  │
    │  API  │           │   (BI)    │
    │ :5000 │           │  :3000    │
    └───┬───┘           └────┬──────┘
        │                    │
        └────────┬───────────┘
                 │
          ┌──────▼──────┐
          │  PostgreSQL │
          │     :5432   │
          └─────────────┘
```

---

## Monitoring & Logs

### Heroku
```bash
# Real-time logs
heroku logs --tail --app your-app-name

# Metrics dashboard
heroku metrics --app your-app-name
```

### AWS Elastic Beanstalk
```bash
# View logs
eb logs --all

# SSH into instance
eb ssh

# CloudWatch metrics
# Dashboard: https://console.aws.amazon.com/cloudwatch
```

### DigitalOcean
```bash
# Stream logs
doctl apps logs <app-id> api --follow

# View insights
# Dashboard: https://cloud.digitalocean.com/apps/<app-id>/insights
```

---

## Backup & Disaster Recovery

### Database Backups

**Heroku:**
```bash
heroku pg:backups:capture --app your-app-name
heroku pg:backups --app your-app-name
```

**AWS:**
```bash
aws rds create-db-snapshot \
  --db-instance-identifier ecommerce-postgres \
  --db-snapshot-identifier backup-$(date +%Y%m%d)
```

**DigitalOcean:**
```bash
doctl databases backup create <db-id>
doctl databases backup list <db-id>
```

### Restore from Backup

```bash
# Heroku
heroku pg:backups:restore <backup-id> --app your-app-name

# AWS
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ecommerce-restore \
  --db-snapshot-identifier backup-20231207

# DigitalOcean
doctl databases backup restore <db-id> <backup-id>
```

---

## Scaling for Production

### Heroku
```bash
# Scale web dyno
heroku ps:scale web=2 --app your-app-name

# Or upgrade instance size
heroku dyno:type web=standard-1x --app your-app-name
```

### AWS Elastic Beanstalk
```bash
# Scale instances
eb scale 2

# Configure auto-scaling
eb config  # Edit aws:autoscaling:asg properties
```

### DigitalOcean
```bash
# Edit .do/app.yaml
instance_count: 2          # Number of instances
instance_size_slug: basic-m  # Larger instance

# Update
doctl apps update <app-id> --spec .do/app.yaml
```

---

## Custom Domain Setup

### 1. Register Domain
- GoDaddy, Route 53, Namecheap, etc.

### 2. Point to Platform

**Heroku:**
```bash
heroku domains:add yourdomain.com --app your-app-name
```
Then update DNS:
- Type: CNAME
- Name: www
- Value: your-app-name.herokuapp.com

**AWS:**
```bash
# Use Route 53 (in AWS Console)
# Create alias record pointing to EB endpoint
```

**DigitalOcean:**
```bash
# In App Settings → Domain
# Add yourdomain.com
# Update DNS CNAME record
```

---

## SSL/TLS Certificates

All platforms provide **free SSL/TLS**:
- ✅ Heroku: Auto-enabled
- ✅ AWS EB: Auto-issued (AWS Certificate Manager)
- ✅ DigitalOcean: Auto-issued

Access via HTTPS automatically:
```
https://your-app.example.com
```

---

## Performance Optimization

### Database Optimization
```sql
-- Add indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_events_user_id ON events(user_id);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = '...';
```

### Caching
Add Redis for caching (optional):

```python
# In app.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/analytics/revenue')
@cache.cached(timeout=300)
def get_revenue():
    # Returns cached data for 5 minutes
    ...
```

### Connection Pooling
SQLAlchemy automatically pools connections:
```python
engine = create_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)
```

---

## Security Best Practices

### Environment Variables
- ✅ Never commit `.env` file
- ✅ Use platform's secure variable management
- ✅ Rotate passwords regularly
- ✅ Use strong, random passwords

### Database Security
- ✅ Enable SSL for database connections
- ✅ Restrict database access to app only
- ✅ Regular backups
- ✅ Enable audit logging

### API Security
- ✅ HTTPS enforced (auto on all platforms)
- ✅ CORS configured
- ✅ Rate limiting (optional)
- ✅ Input validation

```python
# Add rate limiting
from flask_limiter import Limiter

limiter = Limiter(app)

@app.route('/api/etl/load-data', methods=['POST'])
@limiter.limit("5 per hour")
def load_data():
    ...
```

---

## Troubleshooting Guide

### App Won't Start
```bash
# Check logs
# Heroku: heroku logs --tail
# AWS: eb logs --all
# DO: doctl apps logs <app-id> api --follow

# Common issues:
# 1. Missing environment variables
# 2. Database not reachable
# 3. Port binding issue
# 4. Missing dependencies
```

### Database Connection Failed
```bash
# Verify database is running
# Check connection string
# Verify credentials
# Check security group/firewall rules
# Test locally: psql <connection-string>
```

### Slow Performance
```bash
# Check logs for errors
# Monitor CPU/Memory usage
# Analyze slow queries (EXPLAIN ANALYZE)
# Add database indexes
# Scale application/database
```

### Out of Memory
```bash
# Scale to larger instance
# Reduce connection pool size
# Enable query result caching
# Use pagination for large datasets
```

---

## Cost Optimization

### Free Tier Options
- **Heroku**: $7-50/mo (no free tier)
- **AWS**: $100-300/mo free tier (new accounts)
- **DigitalOcean**: $5/mo minimum (free $200 credit for new users)

### Cost Reduction
1. Start with smallest instance type
2. Use shared database (not Multi-AZ)
3. Reduce backup frequency
4. Monitor and scale down if unused
5. Use cheaper storage for non-critical data

### Monthly Budget Examples

**Development:**
- DigitalOcean: ~$25/mo
- AWS Free Tier: Free first year
- Heroku: ~$50/mo

**Production:**
- DigitalOcean: ~$50/mo (scale up)
- AWS: ~$100-200/mo
- Heroku: ~$150-300/mo

---

## Next Steps After Deployment

1. **Set Up Monitoring**
   - CloudWatch (AWS)
   - Datadog
   - New Relic
   - Custom dashboards

2. **Enable Logging**
   - Application logs
   - Database logs
   - Access logs

3. **Configure Backups**
   - Daily automated backups
   - Test restore procedure
   - Keep backup retention policy

4. **Schedule ETL Jobs**
   - Heroku Scheduler
   - AWS Lambda + CloudWatch Events
   - DigitalOcean Scheduled Jobs

5. **Set Up CI/CD**
   - GitHub Actions (already configured)
   - Auto-deploy on push
   - Run tests before deploy

6. **Add Custom Domain**
   - Register domain
   - Configure DNS
   - Enable SSL/TLS (auto)

7. **Team Access**
   - Grant dashboard access
   - Share API documentation
   - Set up issue tracking

---

## Support & Resources

| Resource | Link |
|----------|------|
| Heroku Docs | https://devcenter.heroku.com/ |
| AWS Documentation | https://aws.amazon.com/documentation/ |
| DigitalOcean Docs | https://docs.digitalocean.com/ |
| Flask Documentation | https://flask.palletsprojects.com/ |
| SQLAlchemy | https://docs.sqlalchemy.org/ |
| PostgreSQL | https://www.postgresql.org/docs/ |

---

## Platform Recommendation

**Choose based on your needs:**

🚀 **Heroku** → Best for quick prototyping, non-critical apps  
🏢 **AWS** → Best for enterprise, complex scaling needs  
💰 **DigitalOcean** → Best for cost-conscious, straightforward deployments

---

**Status:** ✅ Ready to Deploy  
**Last Updated:** December 7, 2025  
**Tested Platforms:** Heroku, AWS Elastic Beanstalk, DigitalOcean App Platform
