"""
Initial Alembic migration – creates all tables defined in ``models.py``.
The migration uses ``Base.metadata`` which already contains the models'
Table objects.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

# Revision identifiers, used by Alembic.
revision = "20240507_01_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables defined in the SQLAlchemy models.
    Using ``Base.metadata.create_all`` ensures the schema stays in sync
    with the model definitions.
    """
    # Bind the migration context's engine to the Base metadata.
    bind = op.get_bind()
    from database import Base  # Import after bind is available
    Base.metadata.create_all(bind)


def downgrade() -> None:
    """Drop all tables – reverse of ``upgrade``.
    Alembic will drop tables in the correct order based on foreign‑key
    dependencies.
    """
    bind = op.get_bind()
    from database import Base
    Base.metadata.drop_all(bind)
