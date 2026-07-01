"""create core tables (users, scenarios, conversations, messages, corrections, progress, exercises)

Revision ID: 0001
Revises:
Create Date: 2026-07-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("nom", sa.String(), nullable=True),
        sa.Column("niveau_cecrl", sa.String(), server_default="A1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("titre", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("niveau_cecrl", sa.String(), server_default="A1"),
        sa.Column("contexte", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id"), nullable=True, index=True
        ),
        sa.Column("titre", sa.String(), nullable=True),
        sa.Column("niveau_cecrl", sa.String(), server_default="A1"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "conversation_id",
            sa.Integer(),
            sa.ForeignKey("conversations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("audio_url", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "corrections",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=False, index=True
        ),
        sa.Column("erreur_originale", sa.Text(), nullable=False),
        sa.Column("texte_corrige", sa.Text(), nullable=False),
        sa.Column("explication", sa.Text(), nullable=True),
        sa.Column("type_erreur", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "progress",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("niveau_actuel", sa.String(), server_default="A1"),
        sa.Column("conversations_completees", sa.Integer(), server_default="0"),
        sa.Column("total_messages", sa.Integer(), server_default="0"),
        sa.Column("total_corrections", sa.Integer(), server_default="0"),
        sa.Column("erreurs_frequentes", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id"), nullable=True, index=True
        ),
        sa.Column("niveau_cecrl", sa.String(), server_default="A1"),
        sa.Column("type_exercice", sa.String(), nullable=False),
        sa.Column("contenu", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("exercises")
    op.drop_table("progress")
    op.drop_table("corrections")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("scenarios")
    op.drop_table("users")
