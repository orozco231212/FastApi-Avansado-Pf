"""add authentication fields to users

Revision ID: a2c51e9d043b
Revises: 6f13097d5c18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a2c51e9d043b"
down_revision: Union[str, Sequence[str], None] = "6f13097d5c18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET hashed_password = '!' WHERE hashed_password IS NULL")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("hashed_password", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("hashed_password")