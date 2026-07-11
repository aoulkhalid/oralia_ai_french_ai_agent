"""add niveau_historique table (Phase 6 - progress dashboard)

Ajoute la table niveau_historique, qui trace chaque changement de niveau
CECRL d'un utilisateur au fil du temps, pour alimenter le graphique de
progression du tableau de bord.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "niveau_historique",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("niveau", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_niveau_historique_user_id", "niveau_historique", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_niveau_historique_user_id", table_name="niveau_historique")
    op.drop_table("niveau_historique")
