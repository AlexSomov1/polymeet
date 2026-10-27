"""Categories, meetings, and the persistent geocoding cache.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("slug", name=op.f("uq_categories_slug")),
    )
    op.bulk_insert(
        categories,
        [
            {"id": 1, "slug": "lecture", "title": "Лекция"},
            {"id": 2, "slug": "games", "title": "Игры"},
            {"id": 3, "slug": "concert", "title": "Концерт"},
            {"id": 4, "slug": "sport", "title": "Спорт"},
            {"id": 5, "slug": "walk", "title": "Прогулка"},
            {"id": 6, "slug": "other", "title": "Другое"},
        ],
    )

    op.create_table(
        "meetings",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("organizer_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.SmallInteger(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("address_hint", sa.Text(), nullable=True),
        sa.Column("address_norm", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(precision=53), nullable=True),
        sa.Column("lon", sa.Float(precision=53), nullable=True),
        sa.Column("geo_status", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("capacity", sa.SmallInteger(), nullable=False),
        sa.Column("accepted_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("auto_accept", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('russian', title || ' ' || description)", persisted=True),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meetings")),
        sa.ForeignKeyConstraint(
            ["organizer_id"], ["users.id"], name=op.f("fk_meetings_organizer_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["category_id"], ["categories.id"], name=op.f("fk_meetings_category_id_categories")
        ),
        sa.CheckConstraint("status BETWEEN 0 AND 3", name=op.f("ck_meetings_status")),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 3 AND 120", name=op.f("ck_meetings_title_length")
        ),
        sa.CheckConstraint(
            "char_length(description) <= 2000", name=op.f("ck_meetings_description_length")
        ),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 15 AND 720", name=op.f("ck_meetings_duration_minutes")
        ),
        sa.CheckConstraint(
            "char_length(address) BETWEEN 3 AND 300", name=op.f("ck_meetings_address_length")
        ),
        sa.CheckConstraint(
            "char_length(address_hint) <= 200", name=op.f("ck_meetings_address_hint_length")
        ),
        sa.CheckConstraint(
            "(lat IS NULL) = (lon IS NULL)", name=op.f("ck_meetings_coordinates_together")
        ),
        sa.CheckConstraint("lat BETWEEN -90 AND 90", name=op.f("ck_meetings_latitude")),
        sa.CheckConstraint("lon BETWEEN -180 AND 180", name=op.f("ck_meetings_longitude")),
        sa.CheckConstraint("geo_status BETWEEN 0 AND 3", name=op.f("ck_meetings_geo_status")),
        sa.CheckConstraint("capacity BETWEEN 2 AND 100", name=op.f("ck_meetings_capacity")),
        sa.CheckConstraint(
            "accepted_count BETWEEN 0 AND capacity", name=op.f("ck_meetings_accepted_count")
        ),
    )
    op.create_index(
        "ix_meetings_feed", "meetings", ["starts_at", "id"], postgresql_where=sa.text("status = 1")
    )
    op.create_index(
        "ix_meetings_category_feed",
        "meetings",
        ["category_id", "starts_at", "id"],
        postgresql_where=sa.text("status = 1"),
    )
    op.create_index(
        "ix_meetings_geo",
        "meetings",
        [sa.text("ll_to_earth(lat, lon)")],
        postgresql_using="gist",
        postgresql_where=sa.text("status = 1 AND lat IS NOT NULL"),
    )
    op.create_index("ix_meetings_search", "meetings", ["search_vector"], postgresql_using="gin")
    op.create_index(
        "ix_meetings_organizer",
        "meetings",
        ["organizer_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )

    op.create_table(
        "geocode_cache",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("query_hash", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("address_norm", sa.Text(), nullable=True),
        sa.Column("lat", sa.Float(precision=53), nullable=False),
        sa.Column("lon", sa.Float(precision=53), nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_geocode_cache")),
        sa.UniqueConstraint("query_hash", name=op.f("uq_geocode_cache_query_hash")),
    )


def downgrade() -> None:
    op.drop_table("geocode_cache")
    op.drop_index("ix_meetings_organizer", table_name="meetings")
    op.drop_index("ix_meetings_search", table_name="meetings")
    op.drop_index("ix_meetings_geo", table_name="meetings")
    op.drop_index("ix_meetings_category_feed", table_name="meetings")
    op.drop_index("ix_meetings_feed", table_name="meetings")
    op.drop_table("meetings")
    op.drop_table("categories")
