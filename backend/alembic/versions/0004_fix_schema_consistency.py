"""fix schema consistency after 9a9611e31c70

The 9a9611e31c70 migration (an autogenerate run after a model refactor)
dropped several columns that the rest of the codebase still depends on,
and added a unique constraint that doesn't match the business rules
(a message can have more than one grammar correction). This migration
repairs that drift:

- users.is_active: re-added. auth.py, deps.py and UserOut all use it.
- conversations.ended_at: re-added. chat.py's close_conversation()
  endpoint and ConversationOut both need it.
- corrections.message_id: unique constraint dropped. A single user
  message can contain several distinct grammar errors, so it must be
  possible to store more than one Correction per Message.

Revision ID: 0004
Revises: 9a9611e31c70
Create Date: 2026-07-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "9a9611e31c70"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "conversations",
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    # La contrainte unique a été créée avec un nom auto-généré (None) dans
    # 9a9611e31c70 ; on la supprime via SQL brut pour ne pas dépendre du nom
    # exact attribué par Postgres.
    op.execute("ALTER TABLE corrections DROP CONSTRAINT IF EXISTS corrections_message_id_key")
    op.create_index(
        op.f("ix_corrections_message_id"), "corrections", ["message_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_corrections_message_id"), table_name="corrections")
    op.create_unique_constraint(None, "corrections", ["message_id"])

    op.drop_column("conversations", "ended_at")
    op.drop_column("users", "is_active")
