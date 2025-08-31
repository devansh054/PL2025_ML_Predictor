# 🚀 Premier League Predictor - Production Deployment Guide

## Overview
This guide covers deploying your FAANG-level Premier League Predictor to production environments using modern DevOps practices.

## 📋 Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (local or cloud)
- Node.js 18+ and Python 3.9+
- Redis server
- PostgreSQL database (optional)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Frontend      │────│   Backend API   │
│   (Nginx)       │    │   (Next.js)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │────│   PostgreSQL    │
                       │   (Caching)     │    │   (Database)    │
                       └─────────────────┘    └─────────────────┘
```

## 🐳 Docker Deployment

### 1. Build and Run with Docker Compose

```bash
# Build all services
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backend=3
```

### 2. Individual Container Commands

```bash
# Build frontend
docker build -f Dockerfile.frontend -t pl-predictor-frontend .

# Build backend
docker build -f Dockerfile.backend -t pl-predictor-backend .

# Run frontend
docker run -p 3000:3000 pl-predictor-frontend

# Run backend
docker run -p 8000:8000 pl-predictor-backend
```

## ☸️ Kubernetes Deployment

### 1. Apply Kubernetes Manifests

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Deploy secrets
kubectl apply -f kubernetes/secrets.yaml

# Deploy backend
kubectl apply -f kubernetes/deployment-backend.yaml

# Deploy frontend
kubectl apply -f kubernetes/deployment-frontend.yaml

# Check deployments
kubectl get pods -n pl-predictor
```

### 2. Scaling and Updates

```bash
# Scale backend pods
kubectl scale deployment backend --replicas=5 -n pl-predictor

# Rolling update
kubectl set image deployment/backend backend=pl-predictor-backend:v2.0 -n pl-predictor

# Check rollout status
kubectl rollout status deployment/backend -n pl-predictor
```

## 🌐 Cloud Deployment Options

### AWS EKS
```bash
# Create EKS cluster
eksctl create cluster --name pl-predictor --region us-west-2

# Deploy to EKS
kubectl apply -f kubernetes/ -n pl-predictor

# Setup load balancer
kubectl apply -f kubernetes/ingress-aws.yaml
```

### Google GKE
```bash
# Create GKE cluster
gcloud container clusters create pl-predictor --zone us-central1-a

# Deploy application
kubectl apply -f kubernetes/ -n pl-predictor

# Setup ingress
kubectl apply -f kubernetes/ingress-gcp.yaml
```

### Azure AKS
```bash
# Create AKS cluster
az aks create --resource-group myResourceGroup --name pl-predictor

# Get credentials
az aks get-credentials --resource-group myResourceGroup --name pl-predictor

# Deploy
kubectl apply -f kubernetes/ -n pl-predictor
```

## 📊 Monitoring Setup

### 1. Prometheus & Grafana

```bash
# Install Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

### 2. Application Metrics

```bash
# View application metrics
curl http://localhost:8000/metrics

# Custom dashboards available at:
# - System Performance: /grafana/d/system
# - ML Model Metrics: /grafana/d/ml-models
# - API Performance: /grafana/d/api
```

## 🔒 Security Configuration

### 1. Environment Variables

```bash
# Production environment variables
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://host:6379"
export SECRET_KEY="your-secret-key"
export ML_MODEL_PATH="/app/models"
export LOG_LEVEL="INFO"
```

### 2. SSL/TLS Setup

```yaml
# kubernetes/ingress-tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pl-predictor-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - pl-predictor.yourdomain.com
    secretName: pl-predictor-tls
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and Push Images
      run: |
        docker build -f Dockerfile.backend -t ${{ secrets.REGISTRY }}/backend:${{ github.sha }} .
        docker build -f Dockerfile.frontend -t ${{ secrets.REGISTRY }}/frontend:${{ github.sha }} .
        docker push ${{ secrets.REGISTRY }}/backend:${{ github.sha }}
        docker push ${{ secrets.REGISTRY }}/frontend:${{ github.sha }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl set image deployment/backend backend=${{ secrets.REGISTRY }}/backend:${{ github.sha }}
        kubectl set image deployment/frontend frontend=${{ secrets.REGISTRY }}/frontend:${{ github.sha }}
```

## 📈 Performance Optimization

### 1. Caching Strategy

```python
# Redis caching configuration
REDIS_CONFIG = {
    "host": "redis-cluster",
    "port": 6379,
    "db": 0,
    "decode_responses": True,
    "max_connections": 100
}

# Cache TTL settings
CACHE_TTL = {
    "predictions": 300,      # 5 minutes
    "team_stats": 3600,      # 1 hour
    "model_metrics": 1800    # 30 minutes
}
```

### 2. Database Optimization

```sql
-- PostgreSQL indexes for performance
CREATE INDEX idx_matches_team_date ON matches(team, date);
CREATE INDEX idx_predictions_created ON predictions(created_at);
CREATE INDEX idx_team_stats_season ON team_stats(season, team);
```

### 3. API Rate Limiting

```python
# FastAPI rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/predict")
@limiter.limit("10/minute")
async def predict_match(request: Request, prediction: PredictionRequest):
    # Prediction logic
    pass
```

## 🔍 Health Checks & Monitoring

### 1. Health Check Endpoints

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "dependencies": {
            "database": await check_database(),
            "redis": await check_redis(),
            "ml_model": check_model_loaded()
        }
    }
```

### 2. Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

## 🛠️ Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   ```bash
   kubectl logs <pod-name> -n pl-predictor
   kubectl describe pod <pod-name> -n pl-predictor
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   kubectl exec -it <backend-pod> -- python -c "import psycopg2; print('DB OK')"
   ```

3. **Redis Connection Issues**
   ```bash
   # Test Redis connectivity
   kubectl exec -it <backend-pod> -- redis-cli ping
   ```

### Performance Issues

1. **High Memory Usage**
   ```bash
   # Check resource usage
   kubectl top pods -n pl-predictor
   
   # Adjust resource limits
   kubectl patch deployment backend -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
   ```

2. **Slow API Responses**
   ```bash
   # Check API metrics
   curl http://localhost:8000/metrics | grep http_request_duration
   
   # Enable query optimization
   kubectl set env deployment/backend ENABLE_QUERY_CACHE=true
   ```

## 📊 Production Metrics

### Key Performance Indicators

- **API Response Time**: < 200ms (95th percentile)
- **Prediction Accuracy**: > 80%
- **System Uptime**: > 99.9%
- **Cache Hit Rate**: > 90%
- **Concurrent Users**: 1000+

### Monitoring Dashboards

1. **System Overview**: CPU, Memory, Network, Disk usage
2. **Application Metrics**: Request rates, error rates, response times
3. **ML Model Performance**: Accuracy trends, prediction confidence
4. **Business Metrics**: Daily predictions, user engagement

## 🔄 Backup & Recovery

### Database Backups

```bash
# Automated PostgreSQL backups
kubectl create cronjob db-backup --image=postgres:13 --schedule="0 2 * * *" \
  -- pg_dump $DATABASE_URL > /backups/backup-$(date +%Y%m%d).sql
```

### Model Versioning

```python
# MLflow model versioning
import mlflow

# Register new model version
mlflow.register_model("runs:/run-id/model", "pl-predictor-model")

# Deploy specific version
model_version = mlflow.pyfunc.load_model("models:/pl-predictor-model/Production")
```

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations applied
- [ ] Redis cluster configured
- [ ] Monitoring dashboards setup
- [ ] Backup procedures tested
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Team training completed

## 📞 Support & Maintenance

### Log Aggregation
```bash
# Centralized logging with ELK stack
kubectl apply -f monitoring/elasticsearch.yaml
kubectl apply -f monitoring/logstash.yaml
kubectl apply -f monitoring/kibana.yaml
```

### Alerting Rules
```yaml
# Prometheus alerting rules
groups:
- name: pl-predictor
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"
```

This deployment guide ensures your Premier League Predictor runs reliably in production with enterprise-grade monitoring, security, and scalability.
