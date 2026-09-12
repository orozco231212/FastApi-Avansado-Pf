"""create users devices and loans tables"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("serial_number", sa.String(length=100), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("serial_number"),
    )
    op.create_index("ix_devices_device_type", "devices", ["device_type"], unique=False)
    op.create_index("ix_devices_id", "devices", ["id"], unique=False)
    op.create_index("ix_devices_is_available", "devices", ["is_available"], unique=False)
    op.create_index("ix_devices_serial_number", "devices", ["serial_number"], unique=False)
    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("loan_date", sa.DateTime(), nullable=False),
        sa.Column("return_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loans_device_id", "loans", ["device_id"], unique=False)
    op.create_index("ix_loans_id", "loans", ["id"], unique=False)
    op.create_index("ix_loans_status", "loans", ["status"], unique=False)
    op.create_index("ix_loans_user_id", "loans", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("loans")
    op.drop_table("devices")
    op.drop_table("users")