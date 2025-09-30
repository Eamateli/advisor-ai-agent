from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func
from app.models.document import Document
from app.services.embeddings import embedding_service
from app.services.vector_search import vector_search_service
from app.core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

class HybridSearchService:
    """Hybrid search combining keyword (BM25) and vector similarity"""
    
    def __init__(self):
        self.vector_weight = 0.7  # Weight for vector similarity
        self.keyword_weight = 0.3  # Weight for keyword matching
    
    async def hybrid_search(
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
        Perform hybrid search combining vector similarity and keyword matching
        
        Security: All inputs are sanitized, user_id filter prevents data leakage
        """
        if limit is None:
            limit = settings.MAX_CONTEXT_DOCUMENTS
        
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        # Sanitize query to prevent SQL injection
        sanitized_query = self._sanitize_query(query)
        
        # Get vector search results
        vector_results = await vector_search_service.search_documents(
            db=db,
            user_id=user_id,
            query=sanitized_query,
            doc_types=doc_types,
            metadata_filters=metadata_filters,
            limit=limit * 2,  # Get more results to combine
            similarity_threshold=0.5  # Lower threshold for hybrid
        )
        
        # Get keyword search results
        keyword_results = await self._keyword_search(
            db=db,
            user_id=user_id,
            query=sanitized_query,
            doc_types=doc_types,
            metadata_filters=metadata_filters,
            limit=limit * 2
        )
        
        # Combine and rerank results
        combined_results = self._combine_results(
            vector_results,
            keyword_results,
            limit,
            similarity_threshold
        )
        
        logger.info(f"Hybrid search found {len(combined_results)} documents for user {user_id}")
        return combined_results
    
    async def _keyword_search(
        self,
        db: Session,
        user_id: int,
        query: str,
        doc_types: Optional[List[str]] = None,
        metadata_filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Keyword search using PostgreSQL full-text search
        
        Security: Uses parameterized queries to prevent SQL injection
        """
        # Create tsquery from search terms
        search_terms = self._extract_keywords(query)
        
        if not search_terms:
            return []
        
        # Build parameterized query for full-text search
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
                doc_metadata,
                created_at,
                ts_rank(
                    to_tsvector('english', COALESCE(chunk_text, '')),
                    plainto_tsquery('english', :query)
                ) as keyword_score
            FROM documents
            WHERE user_id = :user_id
            AND to_tsvector('english', COALESCE(chunk_text, '')) @@ plainto_tsquery('english', :query)
        """
        
        params = {
            "query": query,
            "user_id": user_id
        }
        
        # Add document type filter
        if doc_types:
            base_query += " AND doc_type = ANY(:doc_types)"
            params["doc_types"] = doc_types
        
        # Add doc_metadata filters (parameterized)
        if metadata_filters:
            # Define allowed metadata keys to prevent injection
            allowed_keys = {
                'source_id', 'doc_type', 'from_email', 'to_email', 
                'subject', 'company', 'contact_id', 'event_id'
            }
            
            for key, value in metadata_filters.items():
                # Validate key against allowlist
                if key not in allowed_keys:
                    logger.warning(f"Rejected metadata filter key: {key}")
                    continue
                    
                # Use parameterized query with validated key
                param_name = f"meta_{key}"
                base_query += f" AND doc_metadata->>'{key}' = :{param_name}"
                params[param_name] = value
        
        base_query += " ORDER BY keyword_score DESC LIMIT :limit"
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
                "doc_metadata": row.doc_metadata,
                "keyword_score": float(row.keyword_score),
                "created_at": row.created_at
            })
        
        return documents
    
    def _combine_results(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        similarity_threshold: float
    ) -> List[Dict]:
        """
        Combine and rerank results using weighted scoring
        
        Formula: final_score = (vector_weight * similarity) + (keyword_weight * keyword_score)
        """
        # Create dict of all results by document ID
        all_results = {}
        
        # Normalize vector scores (already 0-1)
        for doc in vector_results:
            doc_id = doc['id']
            all_results[doc_id] = {
                **doc,
                'vector_score': doc.get('similarity', 0),
                'keyword_score': 0
            }
        
        # Normalize keyword scores (0-1 range)
        max_keyword_score = max([d.get('keyword_score', 0) for d in keyword_results], default=1)
        
        for doc in keyword_results:
            doc_id = doc['id']
            normalized_keyword_score = doc.get('keyword_score', 0) / max_keyword_score if max_keyword_score > 0 else 0
            
            if doc_id in all_results:
                all_results[doc_id]['keyword_score'] = normalized_keyword_score
            else:
                all_results[doc_id] = {
                    **doc,
                    'vector_score': 0,
                    'keyword_score': normalized_keyword_score
                }
        
        # Calculate combined scores
        for doc_id, doc in all_results.items():
            vector_score = doc['vector_score']
            keyword_score = doc['keyword_score']
            
            # Weighted combination
            combined_score = (
                self.vector_weight * vector_score +
                self.keyword_weight * keyword_score
            )
            
            doc['combined_score'] = combined_score
            doc['similarity'] = combined_score  # For consistency
        
        # Sort by combined score
        ranked_results = sorted(
            all_results.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )
        
        # Filter by threshold and limit
        filtered_results = [
            doc for doc in ranked_results
            if doc['combined_score'] >= (similarity_threshold * 0.7)  # Slightly lower threshold
        ][:limit]
        
        return filtered_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be'}
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _sanitize_query(self, query: str) -> str:
        """Sanitize search query to prevent injection attacks"""
        if not query:
            return ""
        
        # Remove SQL special characters
        query = re.sub(r'[;\'"\\]', '', query)
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Limit length to prevent DoS
        max_length = 1000
        if len(query) > max_length:
            query = query[:max_length]
        
        return query.strip()

hybrid_search_service = HybridSearchService()