from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

def create_vector_indexes(db: Session):
    """
    Create vector indexes for fast similarity search
    
    pgvector supports different index types:
    - IVFFlat: Good for < 1M vectors
    - HNSW: Better for > 1M vectors, faster queries but slower builds
    """
    try:
        # Create IVFFlat index for cosine distance
        # Lists parameter should be sqrt(rows) for IVFFlat
        # Starting with 100 lists, can be adjusted based on data size
        
        logger.info("Creating vector index on documents.embedding...")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS documents_embedding_idx 
            ON documents 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        
        # Create additional indexes for filtering
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_user_type 
            ON documents(user_id, doc_type);
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_source 
            ON documents(doc_type, source_id);
        """))
        
        # GIN index for metadata JSON queries
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_metadata 
            ON documents USING gin(metadata);
        """))
        
        db.commit()
        logger.info("Vector indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating vector indexes: {e}")
        db.rollback()
        raise

def optimize_vector_search(db: Session):
    """Run VACUUM ANALYZE to optimize vector search performance"""
    try:
        logger.info("Running VACUUM ANALYZE on documents table...")
        
        # Close transaction to run VACUUM
        db.commit()
        
        # VACUUM can't run in transaction block, so use autocommit
        connection = db.connection()
        connection.execute(text("VACUUM ANALYZE documents;"))
        
        logger.info("Optimization complete")
        
    except Exception as e:
        logger.error(f"Error optimizing vector search: {e}")
        raise