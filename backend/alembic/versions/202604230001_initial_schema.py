"""initial schema

Revision ID: 202604230001
Revises:
Create Date: 2026-04-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202604230001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hcp_interactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hcp_name", sa.String(length=255), nullable=True, index=True),
        sa.Column("interaction_type", sa.String(length=80), nullable=True),
        sa.Column("interaction_date", sa.Date(), nullable=True),
        sa.Column("interaction_time", sa.Time(), nullable=True),
        sa.Column("attendees", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("topics_discussed", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("materials_shared", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("samples_distributed", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("sentiment", sa.String(length=20), nullable=False, server_default="unknown"),
        sa.Column("outcomes", sa.Text(), nullable=True),
        sa.Column("follow_up_actions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("ai_suggested_followups", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_hcp_interactions_hcp_date", "hcp_interactions", ["hcp_name", "interaction_date"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interaction_id", sa.Integer(), sa.ForeignKey("hcp_interactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=80), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_chat_messages_interaction_created", "chat_messages", ["interaction_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_chat_messages_interaction_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_hcp_interactions_hcp_date", table_name="hcp_interactions")
    op.drop_table("hcp_interactions")
