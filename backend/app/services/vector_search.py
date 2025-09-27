from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_
from app.models.document import Document
from app.services.embeddings import embedding_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class VectorSearchService:
    """Handles vector similarity search"""
    
    async def search_documents(
        self,
        db: Session,
        user_id: int,
        query: str,
        doc_types: Optional[List[str]] = None,
        metadata_filters: Optional[Dict] = None,
        limit: int = None,
        similarity_threshold: float = None
    ) -> List[Dict]:
        """
        Search for similar documents using vector similarity
        
        Args:
            db: Database session
            user_id: User ID to filter by
            query: Search query text
            doc_types: Filter by document types (e.g., ['email', 'hubspot_contact'])
            metadata_filters: Additional JSON metadata filters
            limit: Maximum number of results (default: MAX_CONTEXT_DOCUMENTS)
            similarity_threshold: Minimum similarity score (default: SIMILARITY_THRESHOLD)
        
        Returns:
            List of documents with similarity scores
        """
        if limit is None:
            limit = settings.MAX_CONTEXT_DOCUMENTS
        
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        # Generate query embedding
        query_embedding = await embedding_service.generate_embedding(query)
        
        # Build base query with cosine similarity
        # pgvector uses <=> for cosine distance (1 - similarity)
        # So we calculate similarity as (1 - distance)
        base_query = """
            SELECT 
                id,
                user_id,
                doc_type,
                source_id,
                title,
                content,
                chunk_text,
                chunk_index,
                metadata,
                created_at,
                (1 - (embedding <=> :query_embedding::vector)) as similarity
            FROM documents
            WHERE user_id = :user_id
        """
        
        params = {
            "query_embedding": str(query_embedding),
            "user_id": user_id
        }
        
        # Add document type filter
        if doc_types:
            base_query += " AND doc_type = ANY(:doc_types)"
            params["doc_types"] = doc_types
        
        # Add metadata filters
        if metadata_filters:
            for key, value in metadata_filters.items():
                base_query += f" AND metadata->>'{key}' = :{key}"
                params[key] = value
        
        # Add similarity threshold and ordering
        base_query += """
            AND (1 - (embedding <=> :query_embedding::vector)) >= :threshold
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """
        
        params["threshold"] = similarity_threshold
        params["limit"] = limit
        
        # Execute query
        result = db.execute(text(base_query), params)
        rows = result.fetchall()
        
        # Format results
        documents = []
        for row in rows:
            documents.append({
                "id": row.id,
                "doc_type": row.doc_type,
                "source_id": row.source_id,
                "title": row.title,
                "content": row.content,
                "chunk_text": row.chunk_text,
                "chunk_index": row.chunk_index,
                "metadata": row.metadata,
                "similarity": float(row.similarity),
                "created_at": row.created_at
            })
        
        logger.info(f"Vector search found {len(documents)} documents for user {user_id}")
        return documents
    
    async def search_by_metadata(
        self,
        db: Session,
        user_id: int,
        doc_type: str,
        metadata_key: str,
        metadata_value: str
    ) -> List[Document]:
        """Search documents by exact metadata match"""
        query = db.query(Document).filter(
            and_(
                Document.user_id == user_id,
                Document.doc_type == doc_type,
                Document.metadata[metadata_key].astext == metadata_value
            )
        )
        
        return query.all()
    
    def format_context_for_llm(self, documents: List[Dict]) -> str:
        """Format search results into context string for LLM"""
        if not documents:
            return "No relevant information found in your data."
        
        context_parts = []
        
        # Group by source document to avoid repetition
        grouped = {}
        for doc in documents:
            key = f"{doc['doc_type']}:{doc['source_id']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(doc)
        
        for source_key, chunks in grouped.items():
            # Sort chunks by index
            chunks.sort(key=lambda x: x['chunk_index'])
            
            doc_type = chunks[0]['doc_type']
            metadata = chunks[0]['metadata']
            
            # Format based on document type
            if doc_type == 'email':
                context_parts.append(f"\n--- Email ---")
                context_parts.append(f"Subject: {metadata.get('subject', 'N/A')}")
                context_parts.append(f"From: {metadata.get('from_name', '')} <{metadata.get('from_email', '')}>")
                context_parts.append(f"Date: {metadata.get('date', 'N/A')}")
                context_parts.append("\nContent:")
                for chunk in chunks:
                    context_parts.append(chunk['chunk_text'])
            
            elif doc_type == 'hubspot_contact':
                context_parts.append(f"\n--- HubSpot Contact ---")
                context_parts.append(f"Name: {metadata.get('contact_name', 'N/A')}")
                context_parts.append(f"Email: {metadata.get('contact_email', 'N/A')}")
                context_parts.append(f"Company: {metadata.get('company', 'N/A')}")
                context_parts.append("\nDetails:")
                for chunk in chunks:
                    context_parts.append(chunk['chunk_text'])
            
            elif doc_type == 'hubspot_note':
                context_parts.append(f"\n--- HubSpot Note ---")
                if metadata.get('contact_name'):
                    context_parts.append(f"About: {metadata.get('contact_name')}")
                context_parts.append(f"Created by: {metadata.get('created_by', 'N/A')}")
                context_parts.append(f"Date: {metadata.get('created_at', 'N/A')}")
                context_parts.append("\nNote:")
                for chunk in chunks:
                    context_parts.append(chunk['chunk_text'])
        
        return "\n".join(context_parts)

vector_search_service = VectorSearchService()