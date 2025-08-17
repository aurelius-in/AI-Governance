from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    projects,
    providers,
    models,
    prompts,
    policies,
    proxy,
    evaluations,
    datasets,
    requests,
    audit,
    cost
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["llm-proxy"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(requests.router, prefix="/requests", tags=["requests"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(cost.router, prefix="/cost", tags=["cost"])
