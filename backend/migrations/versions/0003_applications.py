"""Заявки на участие во встречах

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("meeting_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.SmallInteger(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meetings.id"],
            name=op.f("fk_applications_meeting_id_meetings"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_applications_user_id_users")
        ),
        sa.CheckConstraint("status BETWEEN 0 AND 4", name=op.f("ck_applications_status")),
        sa.CheckConstraint(
            "char_length(message) <= 300", name=op.f("ck_applications_message_length")
        ),
    )
    op.create_index(
        "uq_applications_once",
        "applications",
        ["meeting_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("status <> 4"),
    )
    op.create_index(
        "ix_applications_queue", "applications", ["meeting_id", "status", "created_at", "id"]
    )
    op.create_index(
        "ix_applications_user",
        "applications",
        ["user_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_applications_user", table_name="applications")
    op.drop_index("ix_applications_queue", table_name="applications")
    op.drop_index("uq_applications_once", table_name="applications")
    op.drop_table("applications")
