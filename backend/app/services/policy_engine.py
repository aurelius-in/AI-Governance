import json
import requests
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy.orm import Session
import redis

from app.core.config import settings

logger = structlog.get_logger()


class PolicyResult:
    def __init__(self, allowed: bool, violations: List[Dict[str, Any]] = None):
        self.allowed = allowed
        self.violations = violations or []


class PolicyEngine:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
        self.opa_url = settings.OPA_URL

    async def check_request(
        self,
        user_id: int,
        project_id: Optional[int],
        provider: str,
        model: str,
        request_data: Dict[str, Any]
    ) -> PolicyResult:
        """Check if a request is allowed based on policies"""
        
        try:
            # Prepare input for OPA
            input_data = {
                "request": {
                    "provider": provider,
                    "model": model,
                    "user_id": user_id,
                    "project_id": project_id,
                    "estimated_cost": request_data.get("estimated_cost", 0.0),
                    "max_tokens": request_data.get("max_tokens", 1000),
                    "messages": request_data.get("messages", []),
                    "prompt": request_data.get("prompt", "")
                },
                "budget": {
                    "daily_limit": 100.0,  # Get from database
                    "monthly_limit": 1000.0
                },
                "allowed_models": ["gpt-3.5-turbo", "gpt-4", "claude-3-sonnet", "gemini-pro"],
                "allowed_providers": ["openai", "anthropic", "google"],
                "limits": {
                    "max_tokens": 4000
                },
                "spend": {
                    "daily": 0.0,  # Get from database
                    "monthly": 0.0
                }
            }
            
            # Call OPA
            response = requests.post(
                f"{self.opa_url}/v1/data/governance",
                json={"input": input_data}
            )
            
            if response.status_code != 200:
                logger.error("OPA request failed", status_code=response.status_code)
                return PolicyResult(allowed=False, violations=[{"type": "opa_error", "message": "Policy engine unavailable"}])
            
            result = response.json()
            
            # Check if request is allowed
            allowed = result.get("result", {}).get("allow", False)
            violations = result.get("result", {}).get("violations", [])
            
            logger.info(
                "Policy check completed",
                user_id=user_id,
                provider=provider,
                model=model,
                allowed=allowed,
                violations_count=len(violations)
            )
            
            return PolicyResult(allowed=allowed, violations=violations)
            
        except Exception as e:
            logger.error("Policy check failed", error=str(e))
            return PolicyResult(allowed=False, violations=[{"type": "policy_error", "message": str(e)}])

    async def get_policy_bundle(self) -> Dict[str, Any]:
        """Get the current policy bundle from OPA"""
        try:
            response = requests.get(f"{self.opa_url}/v1/policies")
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Failed to get policy bundle", status_code=response.status_code)
                return {}
        except Exception as e:
            logger.error("Failed to get policy bundle", error=str(e))
            return {}

    async def update_policy(self, policy_name: str, policy_content: str) -> bool:
        """Update a policy in OPA"""
        try:
            response = requests.put(
                f"{self.opa_url}/v1/policies/{policy_name}",
                data=policy_content,
                headers={"Content-Type": "text/plain"}
            )
            
            if response.status_code == 200:
                logger.info("Policy updated successfully", policy_name=policy_name)
                return True
            else:
                logger.error("Failed to update policy", policy_name=policy_name, status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Failed to update policy", policy_name=policy_name, error=str(e))
            return False

    async def test_policy(self, policy_name: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a policy with sample data"""
        try:
            response = requests.post(
                f"{self.opa_url}/v1/data/{policy_name}",
                json={"input": test_data}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error("Policy test failed", policy_name=policy_name, status_code=response.status_code)
                return {"error": "Policy test failed"}
                
        except Exception as e:
            logger.error("Policy test failed", policy_name=policy_name, error=str(e))
            return {"error": str(e)}
