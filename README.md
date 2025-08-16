# Enterprise AI Governance Dashboard

A production-ready platform for governing enterprise LLM usage with **policies as code, cost controls, audit trails, and safety guardrails**. Includes an **LLM Proxy Gateway** so all AI calls in your organization flow through a single, observable, and compliant entry point.

---

## 🚀 Features

* **LLM Proxy Gateway**
  Route all requests through a central API with allow-lists, rate limits, cost budgets, and region restrictions.

* **Policies as Code**
  Rego/OPA-based policy enforcement (PII handling, token limits, cost controls, region compliance).

* **Guardrails & Safety**
  PII detection and redaction, toxicity/jailbreak detection, prompt watermarking.

* **RBAC & Multi-Tenant**
  Role-based access (Admin, Project Owner, Developer, Auditor) with OIDC/SCIM integration.

* **Observability & Cost Tracking**
  Token usage, spend by provider/model/team, latency/error metrics, violation trends — all in real-time dashboards.

* **Evaluation Harness**
  Run offline and online evaluations with curated datasets to measure accuracy, bias, PII leakage, and cost-per-output.

* **Audit & Compliance**
  Immutable audit logs, policy version history, and evidence export packs for SOC 2, HIPAA, GDPR, ISO 27001.

---

## 🏗️ Architecture

**Tech Stack**

* Backend: FastAPI + Postgres + Redis + OPA
* Frontend: React + TypeScript + Material UI
* Observability: OpenTelemetry + Prometheus + Grafana + Jaeger
* CI/CD: GitHub Actions + Docker
* Auth: OIDC (Azure AD, Okta, Auth0)

**Flow**

1. User/app sends a request → `/proxy`
2. RBAC + Policy checks (OPA)
3. PII scan + redaction
4. Safety filters (toxicity/jailbreak)
5. Request forwarded to provider (OpenAI, Azure, Anthropic, etc.)
6. Logs, cost accounting, and traces recorded

---

## 📂 Repo Structure

```
ai-governance-dashboard/
  frontend/     # React frontend
  backend/      # FastAPI backend
  policies/     # OPA Rego policies
  eval/         # Evaluation datasets & runners
  docs/         # Architecture & runbooks
  docker-compose.yml
  Makefile
```

---

## ⚡ Quick Start (Local Dev)

```bash
# 1. Clone
git clone https://github.com/<your-username>/ai-governance-dashboard.git
cd ai-governance-dashboard

# 2. Setup environment
cp .env.example .env

# 3. Launch services
make up

# 4. Run migrations & seed data
make db-migrate
make seed

# 5. Access
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
# Grafana: http://localhost:3000
```

---

## 🧪 Evaluations

Run offline evaluations to test safety, accuracy, and cost:

```bash
make eval
```

Metrics include:

* PII leakage rate
* Toxicity rate
* Refusal rate
* Cost per 1k tokens
* Regression vs. previous prompt versions

---

## 🔐 Policies as Code (Example)

```rego
package governance.cost

deny[msg] {
  input.spend.daily > input.budget.daily_limit
  msg := sprintf("daily budget exceeded: %v > %v", [input.spend.daily, input.budget.daily_limit])
}
```

---

## 📊 Dashboards

* **Usage**: Requests by project, provider, model
* **Spend**: Daily/monthly cost, budget alerts
* **Violations**: PII, jailbreak, policy denials
* **Latency/Error Rate**: Per model and provider
* **Evaluation Trends**: Accuracy, bias, regression

---

## 🤝 Contributing

PRs are welcome. Please include tests and follow the project’s linting/formatting rules.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🌐 Why this project?

Enterprises adopting LLMs need **governance, cost control, and compliance** at scale. This project demonstrates how to build and deploy a real-world AI governance framework with:

* **Policies as code**
* **Observability & monitoring**
* **Safety guardrails**
* **Audit readiness**

It’s a showcase of **MLOps + AI Architecture** skills for production environments.
