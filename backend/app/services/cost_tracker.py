from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import structlog
from sqlalchemy.orm import Session
import redis

from app.models.request import Request as RequestModel
from app.models.project import CostBudget

logger = structlog.get_logger()


class BudgetResult:
    def __init__(self, allowed: bool, limit: Optional[float] = None, current_spend: float = 0.0):
        self.allowed = allowed
        self.limit = limit
        self.current_spend = current_spend


class CostTracker:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def check_budget(
        self,
        user_id: int,
        project_id: Optional[int],
        estimated_cost: float
    ) -> BudgetResult:
        """Check if a request is within budget limits"""
        
        try:
            # Get project budget
            if project_id:
                budget = self.db.query(CostBudget).filter(
                    CostBudget.project_id == project_id
                ).first()
                
                if budget:
                    # Check daily budget
                    daily_spend = await self._get_daily_spend(project_id)
                    if daily_spend + estimated_cost > budget.daily_limit:
                        return BudgetResult(
                            allowed=False,
                            limit=budget.daily_limit,
                            current_spend=daily_spend
                        )
                    
                    # Check monthly budget
                    monthly_spend = await self._get_monthly_spend(project_id)
                    if monthly_spend + estimated_cost > budget.monthly_limit:
                        return BudgetResult(
                            allowed=False,
                            limit=budget.monthly_limit,
                            current_spend=monthly_spend
                        )
            
            return BudgetResult(allowed=True)
            
        except Exception as e:
            logger.error("Budget check failed", error=str(e))
            return BudgetResult(allowed=True)  # Allow if check fails

    async def record_usage(
        self,
        request_id: str,
        user_id: int,
        project_id: Optional[int],
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_cost: float
    ) -> None:
        """Record usage and cost for a request"""
        
        try:
            # Create request record
            request_record = RequestModel(
                request_id=request_id,
                user_id=user_id,
                project_id=project_id or 1,  # Default project
                provider=provider,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost=total_cost,
                status="completed"
            )
            
            self.db.add(request_record)
            self.db.commit()
            
            # Update cache
            await self._update_spend_cache(project_id, total_cost)
            
            logger.info(
                "Usage recorded",
                request_id=request_id,
                user_id=user_id,
                project_id=project_id,
                cost=total_cost
            )
            
        except Exception as e:
            logger.error("Failed to record usage", error=str(e))
            self.db.rollback()

    async def get_user_spend(
        self,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get spending statistics for a user"""
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            requests = self.db.query(RequestModel).filter(
                RequestModel.user_id == user_id,
                RequestModel.created_at >= start_date
            ).all()
            
            total_spend = sum(req.cost for req in requests)
            total_requests = len(requests)
            
            # Group by provider
            provider_spend = {}
            for req in requests:
                provider_spend[req.provider] = provider_spend.get(req.provider, 0) + req.cost
            
            # Group by model
            model_spend = {}
            for req in requests:
                model_spend[req.model] = model_spend.get(req.model, 0) + req.cost
            
            return {
                "total_spend": total_spend,
                "total_requests": total_requests,
                "provider_spend": provider_spend,
                "model_spend": model_spend,
                "period_days": days
            }
            
        except Exception as e:
            logger.error("Failed to get user spend", error=str(e))
            return {}

    async def get_project_spend(
        self,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get spending statistics for a project"""
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            requests = self.db.query(RequestModel).filter(
                RequestModel.project_id == project_id,
                RequestModel.created_at >= start_date
            ).all()
            
            total_spend = sum(req.cost for req in requests)
            total_requests = len(requests)
            
            # Daily breakdown
            daily_spend = {}
            for req in requests:
                date_key = req.created_at.strftime("%Y-%m-%d")
                daily_spend[date_key] = daily_spend.get(date_key, 0) + req.cost
            
            return {
                "total_spend": total_spend,
                "total_requests": total_requests,
                "daily_spend": daily_spend,
                "period_days": days
            }
            
        except Exception as e:
            logger.error("Failed to get project spend", error=str(e))
            return {}

    async def _get_daily_spend(self, project_id: int) -> float:
        """Get daily spend for a project from cache"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            cache_key = f"daily_spend:{project_id}:{today}"
            
            cached_spend = self.redis.get(cache_key)
            if cached_spend:
                return float(cached_spend)
            
            # Calculate from database
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            requests = self.db.query(RequestModel).filter(
                RequestModel.project_id == project_id,
                RequestModel.created_at >= start_date
            ).all()
            
            daily_spend = sum(req.cost for req in requests)
            
            # Cache for 1 hour
            self.redis.setex(cache_key, 3600, str(daily_spend))
            
            return daily_spend
            
        except Exception as e:
            logger.error("Failed to get daily spend", error=str(e))
            return 0.0

    async def _get_monthly_spend(self, project_id: int) -> float:
        """Get monthly spend for a project from cache"""
        try:
            this_month = datetime.now().strftime("%Y-%m")
            cache_key = f"monthly_spend:{project_id}:{this_month}"
            
            cached_spend = self.redis.get(cache_key)
            if cached_spend:
                return float(cached_spend)
            
            # Calculate from database
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            requests = self.db.query(RequestModel).filter(
                RequestModel.project_id == project_id,
                RequestModel.created_at >= start_date
            ).all()
            
            monthly_spend = sum(req.cost for req in requests)
            
            # Cache for 1 hour
            self.redis.setex(cache_key, 3600, str(monthly_spend))
            
            return monthly_spend
            
        except Exception as e:
            logger.error("Failed to get monthly spend", error=str(e))
            return 0.0

    async def _update_spend_cache(self, project_id: Optional[int], cost: float) -> None:
        """Update spend cache when new requests are made"""
        if not project_id:
            return
            
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            this_month = datetime.now().strftime("%Y-%m")
            
            # Update daily cache
            daily_key = f"daily_spend:{project_id}:{today}"
            current_daily = self.redis.get(daily_key)
            if current_daily:
                new_daily = float(current_daily) + cost
                self.redis.setex(daily_key, 3600, str(new_daily))
            
            # Update monthly cache
            monthly_key = f"monthly_spend:{project_id}:{this_month}"
            current_monthly = self.redis.get(monthly_key)
            if current_monthly:
                new_monthly = float(current_monthly) + cost
                self.redis.setex(monthly_key, 3600, str(new_monthly))
                
        except Exception as e:
            logger.error("Failed to update spend cache", error=str(e))
