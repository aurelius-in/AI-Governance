package governance

import future.keywords.if
import future.keywords.in

# Default allow
default allow := false

# Allow if no violations
allow if {
    not any(violations)
}

# Collect all violations
violations[violation] if {
    violation := {"type": "cost_limit_exceeded", "message": "Daily cost limit exceeded"}
    cost_limit_violation
}

violations[violation] if {
    violation := {"type": "model_not_allowed", "message": "Model not in allowlist"}
    model_violation
}

violations[violation] if {
    violation := {"type": "provider_not_allowed", "message": "Provider not in allowlist"}
    provider_violation
}

violations[violation] if {
    violation := {"type": "token_limit_exceeded", "message": "Token limit exceeded"}
    token_limit_violation
}

violations[violation] if {
    violation := {"type": "pii_detected", "message": "PII detected in input"}
    pii_violation
}

violations[violation] if {
    violation := {"type": "toxicity_detected", "message": "Toxic content detected"}
    toxicity_violation
}

# Cost limit checks
cost_limit_violation if {
    input.request.estimated_cost > input.budget.daily_limit
}

# Model allowlist checks
model_violation if {
    not input.request.model in input.allowed_models
}

# Provider allowlist checks
provider_violation if {
    not input.request.provider in input.allowed_providers
}

# Token limit checks
token_limit_violation if {
    input.request.max_tokens > input.limits.max_tokens
}

# PII detection (basic regex patterns)
pii_violation if {
    contains_pii(input.request.messages)
}

contains_pii(messages) if {
    message := messages[_]
    contains_pii_pattern(message.content)
}

contains_pii_pattern(content) if {
    # Email pattern
    re_match("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", content)
}

contains_pii_pattern(content) if {
    # Phone number pattern
    re_match("\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b", content)
}

contains_pii_pattern(content) if {
    # SSN pattern
    re_match("\\b\\d{3}-\\d{2}-\\d{4}\\b", content)
}

# Toxicity detection (basic keyword patterns)
toxicity_violation if {
    contains_toxic_content(input.request.messages)
}

contains_toxic_content(messages) if {
    message := messages[_]
    contains_toxic_keywords(message.content)
}

contains_toxic_keywords(content) if {
    toxic_keywords := ["hate", "violence", "discrimination", "harassment"]
    keyword := toxic_keywords[_]
    contains(keyword, content)
}

# Budget tracking
daily_spend := sum([cost | cost := input.spend.daily])
monthly_spend := sum([cost | cost := input.spend.monthly])

# Cost alerts
cost_alert if {
    daily_spend > input.budget.daily_limit * 0.8  # 80% threshold
}

cost_alert if {
    monthly_spend > input.budget.monthly_limit * 0.8  # 80% threshold
}

# Usage analytics
total_requests := count(input.requests)
unique_users := count(input.users)
avg_cost_per_request := daily_spend / total_requests

# Model usage distribution
model_usage[model] := count([req | req := input.requests[_]; req.model == model])

# Provider usage distribution
provider_usage[provider] := count([req | req := input.requests[_]; req.provider == provider])

# User activity
user_activity[user_id] := count([req | req := input.requests[_]; req.user_id == user_id])

# Project usage
project_usage[project_id] := count([req | req := input.requests[_]; req.project_id == project_id])
