from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.rag_pipeline import rag_pipeline
from app.services.vector_search import vector_search_service
from app.services.hybrid_search import hybrid_search_service

router = APIRouter(prefix="/rag", tags=["RAG"])

# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    doc_types: Optional[List[str]] = None
    limit: int = 10
    use_hybrid: bool = False

class SearchResponse(BaseModel):
    query: str
    documents: List[dict]
    formatted_context: str
    document_count: int

# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Search documents using vector similarity or hybrid search
    
    - **query**: Search query text
    - **doc_types**: Filter by document types (email, hubspot_contact, hubspot_note)
    - **limit**: Maximum results
    - **use_hybrid**: Use hybrid search (keyword + vector)
    """
    try:
        if request.use_hybrid:
            documents = await hybrid_search_service.hybrid_search(
                db=db,
                user_id=user.id,
                query=request.query,
                doc_types=request.doc_types,
                limit=request.limit
            )
        else:
            documents = await vector_search_service.search_documents(
                db=db,
                user_id=user.id,
                query=request.query,
                doc_types=request.doc_types,
                limit=request.limit
            )
        
        formatted_context = vector_search_service.format_context_for_llm(documents)
        
        return SearchResponse(
            query=request.query,
            documents=documents,
            formatted_context=formatted_context,
            document_count=len(documents)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_rag_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get RAG statistics for the current user"""
    from app.models.document import Document
    from app.models.email import Email
    from app.models.hubspot import HubSpotContact, HubSpotNote
    
    stats = {
        "total_documents": db.query(Document).filter(Document.user_id == user.id).count(),
        "total_emails": db.query(Email).filter(Email.user_id == user.id).count(),
        "processed_emails": db.query(Email).filter(
            Email.user_id == user.id,
            Email.is_processed == True
        ).count(),
        "total_contacts": db.query(HubSpotContact).filter(HubSpotContact.user_id == user.id).count(),
        "total_notes": db.query(HubSpotNote).filter(HubSpotNote.user_id == user.id).count(),
    }
    
    return stats