"""phase 7+8: exercises, scenarios, gamification, teacher mode, plan

- exercises: user_id, reponse_utilisateur, is_correct, created_at
- scenarios: categorie (regroupement DELF/TCF/quotidien...)
- progress: points, streak_jours, derniere_activite (gamification)
- users: role (student/teacher), plan (free/premium)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- exercises ---
    op.add_column(
        "exercises",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
    )
    op.add_column("exercises", sa.Column("reponse_utilisateur", sa.String(), nullable=True))
    op.add_column("exercises", sa.Column("is_correct", sa.Boolean(), nullable=True))
    op.add_column(
        "exercises",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_exercises_user_id", "exercises", ["user_id"])

    # --- scenarios ---
    op.add_column(
        "scenarios",
        sa.Column("categorie", sa.String(), nullable=True, server_default="quotidien"),
    )

    # --- progress (gamification) ---
    op.add_column(
        "progress",
        sa.Column("points", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "progress",
        sa.Column("streak_jours", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("progress", sa.Column("derniere_activite", sa.Date(), nullable=True))

    # --- users (rôle + plan) ---
    op.add_column(
        "users",
        sa.Column("role", sa.String(), nullable=False, server_default="student"),
    )
    op.add_column(
        "users",
        sa.Column("plan", sa.String(), nullable=False, server_default="free"),
    )

    # --- Scénarios de démarrage (Phase 7) ---
    scenarios_table = sa.table(
        "scenarios",
        sa.column("titre", sa.String),
        sa.column("description", sa.String),
        sa.column("niveau_cecrl", sa.String),
        sa.column("contexte_prompt", sa.String),
        sa.column("categorie", sa.String),
    )
    op.bulk_insert(
        scenarios_table,
        [
            {
                "titre": "Au restaurant",
                "description": "Commander un repas et discuter avec le serveur.",
                "niveau_cecrl": "A1",
                "contexte_prompt": (
                    "Tu joues le rôle d'un serveur dans un restaurant français. "
                    "Accueille le client, propose le menu, prends sa commande, "
                    "réponds à ses questions sur les plats."
                ),
                "categorie": "quotidien",
            },
            {
                "titre": "Entretien d'embauche",
                "description": "Simuler un entretien d'embauche en français.",
                "niveau_cecrl": "B1",
                "contexte_prompt": (
                    "Tu joues le rôle d'un recruteur menant un entretien "
                    "d'embauche. Pose des questions professionnelles classiques "
                    "(parcours, motivations, forces/faiblesses) et réagis aux "
                    "réponses du candidat de façon réaliste."
                ),
                "categorie": "professionnel",
            },
            {
                "titre": "DELF B1 — Épreuve orale (production individuelle)",
                "description": "Entraînement à la production orale du DELF B1 : exprimer et défendre une opinion.",
                "niveau_cecrl": "B1",
                "contexte_prompt": (
                    "Tu es un examinateur DELF B1. Propose un sujet de société "
                    "simple, demande à l'utilisateur son opinion et pourquoi, "
                    "puis pose une question de relance pour qu'il développe et "
                    "nuance son argumentation, comme dans l'épreuve réelle."
                ),
                "categorie": "delf",
            },
            {
                "titre": "TCF — Expression orale, sujet de la vie quotidienne",
                "description": "Entraînement à l'expression orale du TCF sur un sujet familier.",
                "niveau_cecrl": "A2",
                "contexte_prompt": (
                    "Tu es un examinateur TCF. Demande à l'utilisateur de "
                    "décrire une situation de sa vie quotidienne (son quartier, "
                    "sa routine, ses loisirs), avec des questions de "
                    "clarification simples et progressives."
                ),
                "categorie": "tcf",
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM scenarios WHERE titre IN ("
        "'Au restaurant', 'Entretien d''embauche', "
        "'DELF B1 — Épreuve orale (production individuelle)', "
        "'TCF — Expression orale, sujet de la vie quotidienne'"
        ")"
    )

    op.drop_column("users", "plan")
    op.drop_column("users", "role")

    op.drop_column("progress", "derniere_activite")
    op.drop_column("progress", "streak_jours")
    op.drop_column("progress", "points")

    op.drop_column("scenarios", "categorie")

    op.drop_index("ix_exercises_user_id", table_name="exercises")
    op.drop_column("exercises", "created_at")
    op.drop_column("exercises", "is_correct")
    op.drop_column("exercises", "reponse_utilisateur")
    op.drop_column("exercises", "user_id")
