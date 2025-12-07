# Deploy to AWS Elastic Beanstalk

Complete guide to deploy the Ecommerce Analytics Platform to AWS Elastic Beanstalk.

## Prerequisites

- AWS Account (free tier eligible)
- AWS CLI installed: https://aws.amazon.com/cli/
- EB CLI installed: `pip install awsebcli`
- Git repository with all code committed
- IAM user with appropriate permissions

## Step 1: Initial Setup with EB CLI

```bash
# Initialize EB application
eb init -p docker ecommerce-analytics --region us-east-1

# Follow prompts to:
# - Create new application or select existing
# - Choose platform: Docker
# - Enable CodeCommit (optional)
# - Set up SSH access
```

## Step 2: Create Environment

```bash
# Create Elastic Beanstalk environment
eb create ecommerce-prod \
  --instance-type t3.medium \
  --envvars DB_NAME=ecommerce,DB_USER=ecommerce_user \
  --scale 1

# Monitor creation (takes 5-10 minutes)
eb status
```

## Step 3: Set Environment Variables

```bash
# Create secure password
DB_PASSWORD=$(openssl rand -base64 32)
MB_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Set variables in EB
eb setenv \
  DB_HOST=ecommerce-postgres.xxxxx.rds.amazonaws.com \
  DB_PORT=5432 \
  DB_NAME=ecommerce \
  DB_USER=ecommerce_user \
  DB_PASSWORD=$DB_PASSWORD \
  MB_ADMIN_EMAIL=admin@ecommerce.com \
  MB_ADMIN_PASSWORD=$MB_ADMIN_PASSWORD \
  FLASK_ENV=production

# Verify
eb printenv
```

## Step 4: Create RDS PostgreSQL Instance

```bash
# Via AWS Console (recommended for persistence):
# 1. Go to RDS Dashboard
# 2. Create Database
#    - Engine: PostgreSQL 15
#    - Template: Free tier
#    - DB instance identifier: ecommerce-postgres
#    - Master username: ecommerce_user
#    - Auto-generate password OR set custom
# 3. Enable public accessibility: No
# 4. Create DB subnet group
# 5. Create security group allowing EB access

# Or via AWS CLI:
aws rds create-db-instance \
  --db-instance-identifier ecommerce-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username ecommerce_user \
  --master-user-password $DB_PASSWORD \
  --allocated-storage 20 \
  --publicly-accessible false \
  --multi-az false
```

## Step 5: Configure Security Groups

```bash
# Get EB security group ID
EB_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=awseb-e-*" \
  --query 'SecurityGroups[0].GroupId' --output text)

# Get RDS security group ID
RDS_SG=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=default" \
  --query 'SecurityGroups[0].GroupId' --output text)

# Allow EB to connect to RDS
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG \
  --protocol tcp \
  --port 5432 \
  --source-group $EB_SG
```

## Step 6: Deploy Application

```bash
# Deploy to Elastic Beanstalk
eb deploy ecommerce-prod

# Monitor deployment
eb logs --all

# Check environment health
eb health

# Open in browser
eb open
```

## Step 7: Run Initialization

```bash
# SSH into instance
eb ssh

# Inside instance:
python scripts/create_schema.py
python scripts/automate_etl_and_reports.py

# Exit
exit
```

## Step 8: Configure Custom Domain (Optional)

```bash
# Register domain (Route 53, GoDaddy, etc.)

# Update EB with custom domain
eb scale 1  # Ensure at least 1 instance

# Create alias in Route 53
# Point to EB endpoint: ecommerce-prod.elasticbeanstalk.com
```

## Dockerrun.aws.json Configuration

Create `Dockerrun.aws.json` for container configuration:

```json
{
  "AWSEBDockerrunVersion": "1",
  "Image": {
    "Name": "your-account-id.dkr.ecr.region.amazonaws.com/ecommerce-analytics:latest",
    "Update": "true"
  },
  "Ports": [
    {
      "ContainerPort": 5000
    }
  ],
  "Logging": "/var/log"
}
```

## Using AWS ECR (Elastic Container Registry)

```bash
# Create ECR repository
aws ecr create-repository --repository-name ecommerce-analytics

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com

# Build and tag Docker image
docker build -t ecommerce-analytics:latest .
docker tag ecommerce-analytics:latest your-account-id.dkr.ecr.us-east-1.amazonaws.com/ecommerce-analytics:latest

# Push to ECR
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/ecommerce-analytics:latest

# Deploy
eb deploy
```

## AWS Configuration Files

Create `.ebextensions/` directory with:

### `.ebextensions/python.config`
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:autoscaling:asg:
    MaxSize: 3
    MinSize: 1
  aws:elasticbeanstalk:cloudwatch:logs:
    StreamLogs: true
    DeleteOnTerminate: true
    RetentionInDays: 7
```

### `.ebextensions/alb.config`
```yaml
option_settings:
  aws:elbv2:listener:default:
    Protocol: HTTP
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /api/health
    HealthCheckInterval: 30
    HealthyThreshold: 3
    UnhealthyThreshold: 5
```

## Monitoring & Logging

```bash
# View real-time logs
eb logs --all --stream

# View logs in CloudWatch
# AWS Console → CloudWatch → Logs → /aws/elasticbeanstalk/ecommerce-prod

# Enable monitoring
eb config  # Edit and enable Enhanced Health Reporting

# CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElasticBeanstalk \
  --metric-name TargetResponseTime \
  --dimensions Name=EnvironmentName,Value=ecommerce-prod
```

## Useful EB Commands

```bash
# Environment status
eb status

# Print environment variables
eb printenv

# SSH into instance
eb ssh

# View logs
eb logs

# Open app in browser
eb open

# Terminate environment
eb terminate ecommerce-prod

# List environments
eb list

# Scale instances
eb scale 2

# Check health
eb health

# Abort deployment
eb abort
```

## Scaling Configuration

Edit via `eb config`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  AWSEBAutoScalingGroup:
    Properties:
      MinSize: 1
      MaxSize: 4
      DesiredCapacity: 2
```

## Load Balancer Setup

```bash
# Configure ALB rules
eb config

# Set under aws:elasticbeanstalk:environment:load-balancer:
#   LoadBalancerType: application
#   Stickiness Enabled: true
#   Stickiness Duration: 86400
```

## Production Checklist

- ✅ RDS database encrypted
- ✅ RDS Multi-AZ enabled (optional)
- ✅ RDS automated backups enabled
- ✅ Security groups configured correctly
- ✅ SSL/TLS certificate installed
- ✅ CloudWatch monitoring enabled
- ✅ Application logs configured
- ✅ Auto-scaling configured
- ✅ Health check endpoint verified
- ✅ DNS records configured

## Cost Estimation

| Service | Tier | Cost/Month |
|---------|------|-----------|
| EB Instance (t3.medium) | 1x | ~$30 |
| RDS PostgreSQL (db.t3.micro) | 1x | ~$15 |
| Data Transfer | Standard | ~$5-10 |
| **Total** | **Minimal** | **~$50-55** |

## Troubleshooting

### Deployment Failed
```bash
# Check logs
eb logs --all

# Redeploy
eb deploy --verbose
```

### Database Connection Error
```bash
# Verify RDS is running
aws rds describe-db-instances --db-instance-identifier ecommerce-postgres

# Check security group rules
aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupName,IpPermissions]'
```

### High Memory Usage
```bash
# Scale to larger instance
eb scale --timeout 10
eb setenv INSTANCE_TYPE=t3.large

# Or add more instances
eb scale 2
```

## Backup & Restore

```bash
# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier ecommerce-postgres \
  --db-snapshot-identifier ecommerce-backup-$(date +%Y%m%d)

# List snapshots
aws rds describe-db-snapshots

# Restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier ecommerce-restored \
  --db-snapshot-identifier ecommerce-backup-20231207
```

## Additional Resources

- AWS EB Documentation: https://docs.aws.amazon.com/elasticbeanstalk/
- RDS PostgreSQL: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- EB CLI Reference: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html
- Pricing Calculator: https://calculator.aws/
