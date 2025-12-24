"""
API v1 router - aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.audit_logs import router as audit_logs_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.entries import router as entries_router
from app.api.v1.projects import router as projects_router
from app.api.v1.properties import router as properties_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.wikidata import router as wikidata_router

api_router = APIRouter()

# Include all routers with their prefixes and tags
api_router.include_router(datasets_router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(properties_router, prefix="/properties", tags=["Properties"])
api_router.include_router(projects_router, prefix="/projects", tags=["Projects"])
# Custom paths - no prefix needed
api_router.include_router(entries_router, tags=["Entries"])
api_router.include_router(tasks_router, tags=["Tasks"])
api_router.include_router(candidates_router, tags=["Candidates"])
api_router.include_router(audit_logs_router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(wikidata_router, prefix="/wikidata", tags=["Wikidata"])
