"""
Add file metadata columns to uploaded_documents table.
Revision ID: bfc7b46a92e9
Revises: 20240507_01_init
Create Date: 2026-05-07 04:30:28.881107
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'bfc7b46a92e9'
down_revision: str = '20240507_01_init'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to uploaded_documents
    op.add_column('uploaded_documents', sa.Column('file_path', sa.String(), nullable=False))
    op.add_column('uploaded_documents', sa.Column('filename', sa.String(), nullable=False))
    op.add_column('uploaded_documents', sa.Column('mimetype', sa.String(), nullable=False))
    op.add_column('uploaded_documents', sa.Column('filesize', sa.Integer(), nullable=False))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('uploaded_documents', 'file_path')
    op.drop_column('uploaded_documents', 'filename')
    op.drop_column('uploaded_documents', 'mimetype')
    op.drop_column('uploaded_documents', 'filesize')
