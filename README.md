# 🚀 AI Governance Dashboard

A comprehensive **Enterprise AI Governance Platform** with LLM Proxy Gateway, Policies as Code, Safety Guardrails, and Observability.

## ✨ Features

### 🔐 **LLM Proxy Gateway**
- **Multi-Provider Support**: OpenAI, Anthropic, Google, Azure
- **Unified API**: Single endpoint for all LLM providers
- **Request Routing**: Intelligent provider selection
- **Rate Limiting**: Built-in request throttling

### 📋 **Policies as Code (OPA)**
- **Rego Policies**: Declarative governance rules
- **Cost Controls**: Daily/monthly budget limits
- **Model Allowlists**: Provider and model restrictions
- **Token Limits**: Request size controls
- **PII Detection**: Automatic sensitive data detection
- **Toxicity Filtering**: Content safety checks

### 🛡️ **Safety Guardrails**
- **PII Detection & Redaction**: Email, phone, SSN, credit cards
- **Toxicity Detection**: Hate speech, violence, harassment
- **Jailbreak Prevention**: Prompt injection protection
- **Content Filtering**: Real-time safety checks

### 📊 **Observability & Monitoring**
- **OpenTelemetry**: Distributed tracing with Jaeger
- **Prometheus Metrics**: Request rates, costs, violations
- **Grafana Dashboards**: Real-time monitoring
- **Structured Logging**: JSON logs with trace IDs
- **Audit Trails**: Immutable request logs

### 💰 **Cost Management**
- **Real-time Tracking**: Per-request cost calculation
- **Budget Enforcement**: Daily/monthly limits
- **Spend Analytics**: Provider and model breakdowns
- **Alerts**: Budget threshold notifications

### 🔐 **Security & Auth**
- **JWT Authentication**: Secure token-based auth
- **Role-Based Access**: Admin, project owner, developer roles
- **Multi-Tenant**: Organization isolation
- **OIDC Support**: Enterprise SSO integration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │   PostgreSQL DB │
│                 │    │                 │    │                 │
│  - Dashboard    │◄──►│  - LLM Proxy    │◄──►│  - Users        │
│  - Analytics    │    │  - Policies     │    │  - Requests     │
│  - Settings     │    │  - Auth         │    │  - Projects     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │   OPA Engine    │    │   Redis Cache   │
│                 │    │                 │    │                 │
│  - Dashboards   │    │  - Policy Eval  │    │  - Rate Limiting│
│  - Alerts       │    │  - Rules Engine │    │  - Session Store│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📂 Project Structure

```
AI-Governance/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/  # API endpoints
│   │   ├── core/              # Core configuration
│   │   ├── models/            # Database models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic
│   ├── scripts/               # Database scripts
│   ├── main.py               # FastAPI app entry point
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   └── services/        # API services
│   ├── package.json         # Node.js dependencies
│   └── Dockerfile          # Frontend container
├── policies/                 # OPA Rego policies
│   └── governance.rego      # Main governance rules
├── config/                   # Configuration files
│   ├── prometheus.yml       # Prometheus config
│   └── otel-collector-config.yaml # OpenTelemetry config
├── docker-compose.yml       # Local development setup
├── Makefile                 # Development commands
├── env.example              # Environment variables template
└── README.md               # This file
```

## 🚀 Quick Start (Local Dev)

### Prerequisites
- **Docker & Docker Compose**
- **Git**
- **Make** (optional, for convenience)

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd AI-Governance

# Copy environment template
cp env.example .env

# Edit .env with your configuration
# - Add your LLM API keys
# - Configure database URLs
# - Set security keys
```

### 2. Start Development Environment
```bash
# Start all services
make up

# Or manually:
docker-compose up -d
```

### 3. Initialize Database
```bash
# Seed with sample data
make seed

# Or manually:
docker-compose exec backend python scripts/seed_data.py
```

### 4. Access Services
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger**: http://localhost:16686
- **Prometheus**: http://localhost:9090

### 5. Test the System
```bash
# Default credentials:
# Admin: admin@example.com / admin123
# Demo: demo@example.com / demo123

# Test LLM proxy
curl -X POST "http://localhost:8000/api/v1/proxy/chat/completions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "gpt-3.5-turbo",
    "provider": "openai"
  }'
```

## 🛠️ Development Commands

```bash
# Service Management
make up              # Start all services
make down            # Stop all services
make build           # Build all containers
make logs            # View all logs
make clean           # Remove containers and volumes

# Database
make db-migrate      # Run migrations
make db-reset        # Reset database
make seed            # Seed sample data

# Development
make backend-dev     # Start backend in dev mode
make frontend-dev    # Start frontend in dev mode

# Testing
make test            # Run all tests
make test-backend    # Backend tests only
make test-frontend   # Frontend tests only

# Code Quality
make lint            # Run linting
make format          # Format code

# Monitoring
make logs-backend    # Backend logs
make logs-frontend   # Frontend logs
make status          # Service status

# Shell Access
make shell-backend   # Backend container shell
make shell-db        # Database shell
```

## 📊 Monitoring & Observability

### **Grafana Dashboards**
- **Request Metrics**: Rate, latency, error rates
- **Cost Analytics**: Spend by provider, model, user
- **Policy Violations**: Violation trends and types
- **System Health**: Service status and performance

### **Jaeger Tracing**
- **Request Flow**: End-to-end request tracing
- **Service Dependencies**: Inter-service communication
- **Performance Analysis**: Latency breakdowns

### **Prometheus Metrics**
- **Custom Metrics**: Request counts, costs, violations
- **System Metrics**: CPU, memory, disk usage
- **Business Metrics**: User activity, project usage

## 🧪 Evaluation Framework

### **Offline Evaluations**
- **Accuracy Testing**: Model performance on test sets
- **Bias Detection**: Fairness and bias analysis
- **PII Leakage**: Privacy violation testing
- **Cost Analysis**: Cost-per-output optimization

### **Online Evaluations**
- **Real-time Monitoring**: Live request evaluation
- **A/B Testing**: Model comparison
- **User Feedback**: Human evaluation integration

## 🔒 Security Features

### **Authentication & Authorization**
- **JWT Tokens**: Secure stateless authentication
- **Role-Based Access**: Granular permission control
- **OIDC Integration**: Enterprise SSO support
- **Multi-Factor Auth**: Enhanced security

### **Data Protection**
- **PII Detection**: Automatic sensitive data identification
- **Data Encryption**: At-rest and in-transit encryption
- **Audit Logging**: Comprehensive activity tracking
- **Compliance**: GDPR, SOC2, HIPAA support

## 🚀 Production Deployment

### **Docker Deployment**
```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# With external database
docker-compose -f docker-compose.prod.yml -f docker-compose.db.yml up -d
```

### **Kubernetes Deployment**
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Monitor deployment
kubectl get pods -n ai-governance
```

### **Environment Variables**
```bash
# Required for production
POSTGRES_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379
JWT_SECRET_KEY=your-super-secret-key
ENCRYPTION_KEY=your-32-byte-encryption-key

# LLM Provider Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
```

## 📈 Usage Examples

### **Basic LLM Request**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/proxy/chat/completions",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "messages": [{"role": "user", "content": "Explain quantum computing"}],
        "model": "gpt-4",
        "provider": "openai",
        "project_id": 1
    }
)
```

### **Policy Configuration**
```rego
# policies/governance.rego
package governance

# Allow requests under $50 daily budget
allow if {
    input.request.estimated_cost <= 50
    input.request.provider in ["openai", "anthropic"]
    input.request.model in ["gpt-3.5-turbo", "gpt-4"]
}
```

### **Cost Monitoring**
```python
# Get user spending
spend_data = requests.get(
    "http://localhost:8000/api/v1/cost/user/1",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
).json()

print(f"Total spend: ${spend_data['total_spend']}")
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](link-to-wiki)
- **Issues**: [GitHub Issues](link-to-issues)
- **Discussions**: [GitHub Discussions](link-to-discussions)

---

**Built with ❤️ for responsible AI governance**
