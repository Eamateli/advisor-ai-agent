"""add_vector_indexes

Revision ID: b3c3d4969f89
Revises: a34a10da60af
Create Date: 2025-09-27 17:25:12.974909

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c3d4969f89'
down_revision = 'a34a10da60af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create IVFFlat index for vector similarity search
    op.execute("""
        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
        ON documents 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    # Create composite index for user + doc_type filtering
    op.create_index(
        'idx_documents_user_type',
        'documents',
        ['user_id', 'doc_type']
    )
    
    # Create index for source lookups
    op.create_index(
        'idx_documents_source',
        'documents',
        ['doc_type', 'source_id']
    )
    
    # Create GIN index for metadata JSON queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_documents_metadata 
        ON documents USING gin(metadata);
    """)

def downgrade() -> None:
    op.drop_index('idx_documents_metadata', table_name='documents')
    op.drop_index('idx_documents_source', table_name='documents')
    op.drop_index('idx_documents_user_type', table_name='documents')
    op.execute('DROP INDEX IF EXISTS documents_embedding_idx;')