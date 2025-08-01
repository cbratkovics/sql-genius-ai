# SQL Genius AI - Production Deployment Guide

This guide covers deploying SQL Genius AI as a production-ready SaaS platform with multi-tenant architecture, enterprise security, and horizontal scaling capabilities.

## Architecture Overview

The production deployment includes:
- **FastAPI Backend**: Multi-tenant REST API with authentication
- **PostgreSQL**: Primary database with tenant isolation
- **Redis**: Caching and Celery task queue
- **Celery Workers**: Async processing for SQL generation and analysis
- **AWS Infrastructure**: ECS, RDS, ElastiCache, S3, ALB
- **Monitoring**: CloudWatch, Prometheus, Sentry
- **Security**: WAF, SSL/TLS, encryption at rest

## Prerequisites

### Required Accounts & Services
- AWS Account with administrative access
- Stripe account for payment processing
- Anthropic API key for Claude AI
- Domain name for SSL certificate
- Docker and Docker Compose
- AWS CLI configured
- Terraform or AWS CDK (optional)

### Environment Variables
Create a `.env` file with the following variables:

```bash
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=sql_genius_ai
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key (optional)

# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID_PRO=price_your_pro_price_id
STRIPE_PRICE_ID_ENTERPRISE=price_your_enterprise_price_id

# Security
SECRET_KEY=your_32_character_secret_key
ENCRYPTION_KEY=your_32_character_encryption_key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@yourapp.com
EMAILS_FROM_NAME=SQL Genius AI

# Admin User
FIRST_SUPERUSER=admin@yourapp.com
FIRST_SUPERUSER_PASSWORD=your_admin_password

# AWS (for production)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your-s3-bucket
S3_REGION=us-east-1

# Monitoring
SENTRY_DSN=your_sentry_dsn (optional)
```

## Deployment Options

### Option 1: Docker Compose (Development/Small Scale)

1. **Clone and Setup**
```bash
git clone https://github.com/yourusername/sql-genius-ai.git
cd sql-genius-ai
cp .env.example .env
# Edit .env with your values
```

2. **Build and Start Services**
```bash
cd infrastructure/docker
docker-compose up -d
```

3. **Run Database Migrations**
```bash
docker-compose exec backend alembic upgrade head
```

4. **Create First Superuser**
```bash
docker-compose exec backend python -m backend.scripts.create_superuser
```

5. **Access the Application**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555

### Option 2: AWS Production Deployment

#### Step 1: Infrastructure Setup

1. **Deploy CloudFormation Stack**
```bash
aws cloudformation create-stack \
  --stack-name sql-genius-ai-prod \
  --template-body file://infrastructure/aws/cloudformation.yaml \
  --parameters ParameterKey=Environment,ParameterValue=production \
  --capabilities CAPABILITY_IAM
```

2. **Store Secrets in AWS Systems Manager**
```bash
aws ssm put-parameter \
  --name "/sql-genius-ai/database/password" \
  --value "your_secure_db_password" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/sql-genius-ai/anthropic/api-key" \
  --value "your_anthropic_api_key" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/sql-genius-ai/stripe/secret-key" \
  --value "sk_live_your_stripe_key" \
  --type "SecureString"
```

#### Step 2: Container Registry

1. **Create ECR Repository**
```bash
aws ecr create-repository --repository-name sql-genius-ai
```

2. **Build and Push Docker Image**
```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -f infrastructure/docker/Dockerfile.backend -t sql-genius-ai .

# Tag image
docker tag sql-genius-ai:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/sql-genius-ai:latest

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/sql-genius-ai:latest
```

#### Step 3: Database Setup

1. **Connect to RDS Instance**
```bash
# Get RDS endpoint from CloudFormation outputs
aws cloudformation describe-stacks \
  --stack-name sql-genius-ai-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
  --output text
```

2. **Run Migrations**
```bash
# Connect through bastion host or VPN
POSTGRES_HOST=your-rds-endpoint.amazonaws.com python -m alembic upgrade head
```

#### Step 4: SSL Certificate

1. **Request Certificate via ACM**
```bash
aws acm request-certificate \
  --domain-name api.yourapp.com \
  --validation-method DNS \
  --subject-alternative-names "*.yourapp.com"
```

2. **Update Load Balancer with HTTPS Listener**
```bash
# Add HTTPS listener to ALB (via console or CLI)
```

#### Step 5: Monitoring Setup

1. **Configure CloudWatch Alarms**
```bash
# CPU Utilization
aws cloudwatch put-metric-alarm \
  --alarm-name "SQL-Genius-High-CPU" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# Error Rate
aws cloudwatch put-metric-alarm \
  --alarm-name "SQL-Genius-High-Errors" \
  --alarm-description "High error rate" \
  --metric-name 4XXError \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

2. **Set up Log Aggregation**
```bash
# CloudWatch Logs are automatically configured in the CloudFormation template
# Consider setting up log shipping to external services like DataDog or Splunk
```

### Option 3: Kubernetes Deployment

1. **Apply Kubernetes Manifests**
```bash
kubectl apply -f infrastructure/kubernetes/
```

2. **Configure Ingress**
```bash
# Update ingress.yaml with your domain
kubectl apply -f infrastructure/kubernetes/ingress.yaml
```

## Post-Deployment Configuration

### 1. DNS Configuration
Point your domain to the load balancer:
```bash
# Get ALB DNS name
aws elbv2 describe-load-balancers \
  --names sql-genius-ai-prod-alb \
  --query 'LoadBalancers[0].DNSName' \
  --output text

# Create CNAME record: api.yourapp.com -> alb-dns-name
```

### 2. Stripe Webhook Configuration
1. Go to Stripe Dashboard > Webhooks
2. Add endpoint: `https://api.yourapp.com/api/v1/billing/webhook`
3. Select events: `customer.subscription.*`, `invoice.payment_*`
4. Copy webhook secret to environment variables

### 3. Email Configuration
Configure SMTP settings for transactional emails:
- Gmail: Use App Passwords
- SendGrid: Use API key
- AWS SES: Configure IAM role

### 4. Monitoring & Alerting
Set up monitoring dashboards:
```bash
# Example CloudWatch Dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "SQL-Genius-AI" \
  --dashboard-body file://monitoring/cloudwatch-dashboard.json
```

## Security Considerations

### 1. Network Security
- VPC with private subnets for database and cache
- Security groups with minimal required access
- WAF rules for DDoS and SQL injection protection
- VPN or bastion host for database access

### 2. Data Security
- Encryption at rest for RDS and S3
- SSL/TLS for all communications
- Secrets stored in AWS Systems Manager
- Regular security scanning

### 3. Access Control
- IAM roles with least privilege
- Multi-factor authentication for AWS console
- Regular credential rotation
- Audit logging enabled

## Scaling Configuration

### 1. Auto Scaling
```bash
# ECS Service Auto Scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/sql-genius-cluster/sql-genius-api \
  --min-capacity 2 \
  --max-capacity 10

# CPU-based scaling policy  
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/sql-genius-cluster/sql-genius-api \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

### 2. Database Scaling
```bash
# Read replicas for PostgreSQL
aws rds create-db-instance-read-replica \
  --db-instance-identifier sql-genius-read-replica \
  --source-db-instance-identifier sql-genius-prod-db \
  --db-instance-class db.t3.medium
```

### 3. Celery Worker Scaling
```bash
# Scale worker service
aws ecs update-service \
  --cluster sql-genius-cluster \
  --service sql-genius-workers \
  --desired-count 5
```

## Backup & Disaster Recovery

### 1. Database Backups
```bash
# Automated backups are enabled in CloudFormation
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier sql-genius-prod-db \
  --db-snapshot-identifier sql-genius-manual-snapshot-$(date +%Y%m%d)
```

### 2. File Storage Backups
```bash
# S3 Cross-region replication
aws s3api put-bucket-replication \
  --bucket sql-genius-files \
  --replication-configuration file://s3-replication-config.json
```

### 3. Configuration Backups
```bash
# Export CloudFormation template
aws cloudformation get-template \
  --stack-name sql-genius-ai-prod \
  --template-stage Processed > backup-template.yaml
```

## Monitoring & Maintenance

### 1. Health Checks
- Load balancer health checks on `/health`
- Database connection monitoring
- Redis connectivity checks
- Celery worker health monitoring

### 2. Performance Monitoring
- Response time metrics
- Database query performance
- Cache hit rates
- Queue processing times

### 3. Log Management
- Application logs via CloudWatch
- Access logs from ALB
- Database slow query logs
- Error tracking with Sentry

### 4. Regular Maintenance
- Security patches monthly
- Database maintenance windows
- SSL certificate renewal
- Dependency updates

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids sg-xxx

# Test connection
telnet your-db-endpoint.amazonaws.com 5432
```

2. **High Memory Usage**
```bash
# Scale up ECS tasks
aws ecs update-service \
  --cluster sql-genius-cluster \
  --service sql-genius-api \
  --desired-count 4
```

3. **Celery Workers Not Processing**
```bash
# Check Redis connectivity
redis-cli -h your-redis-endpoint.cache.amazonaws.com ping

# Restart workers
aws ecs update-service \
  --cluster sql-genius-cluster \
  --service sql-genius-workers \
  --force-new-deployment
```

### Log Locations
- Application logs: CloudWatch `/aws/ecs/sql-genius`
- Load balancer logs: S3 bucket (if enabled)
- Database logs: CloudWatch `/aws/rds/instance/sql-genius-prod-db/postgresql`

## Cost Optimization

### 1. Right-sizing Resources
- Monitor CPU/memory utilization
- Use Spot instances for dev/staging
- Schedule non-prod environments

### 2. Storage Optimization
- S3 lifecycle policies for old files
- Database storage monitoring
- Redis memory optimization

### 3. Reserved Instances
- Purchase RDS reserved instances
- Use Savings Plans for ECS

## Support & Maintenance

For ongoing support:
1. Monitor CloudWatch alarms
2. Set up automated backup verification
3. Regular security assessments
4. Performance optimization reviews
5. Disaster recovery testing

## License & Compliance

Ensure compliance with:
- SOC 2 Type II requirements
- GDPR for EU customers
- CCPA for California customers
- PCI DSS for payment processing (Stripe handles this)
- HIPAA for healthcare data (if applicable)

This deployment guide provides a production-ready setup for SQL Genius AI with enterprise-grade security, scalability, and monitoring capabilities.