"""
API v1 router - aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.datasets import router as datasets_router

api_router = APIRouter()

# Include all routers with their prefixes and tags
api_router.include_router(datasets_router, prefix="/datasets", tags=["Datasets"])

# Additional routers will be added here as implemented:
# api_router.include_router(properties_router, prefix="/properties", tags=["Properties"])
# api_router.include_router(entries_router, prefix="/entries", tags=["Entries"])
# api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# api_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
# api_router.include_router(candidates_router, tags=["Candidates"])
# api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logs"])
# api_router.include_router(wikidata_router, prefix="/wikidata", tags=["Wikidata"])
