"""
Mode enseignant (Phase 7).

Limitation volontairement assumée pour ce MVP : il n'existe pas encore de
notion de "classe" reliant un enseignant à un sous-ensemble précis
d'élèves — un compte "teacher" voit la progression de TOUS les comptes
"student" de la plateforme. Une vraie gestion de classes (table
`classrooms` + table d'association enseignant/élèves) serait la suite
logique si plusieurs enseignants indépendants utilisent la plateforme.

Pour promouvoir un compte en "teacher" (aucune UI pour l'instant, c'est
une opération d'administration) :
    UPDATE users SET role = 'teacher' WHERE email = 'prof@exemple.com';
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.progress import Progress
from app.services import conversation_service

router = APIRouter(prefix="/teacher", tags=["teacher"])


def _require_teacher(current_user: User) -> None:
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Réservé aux comptes enseignant.",
        )


@router.get("/students")
def list_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste tous les élèves (comptes 'student') avec un résumé de leur progression."""
    _require_teacher(current_user)

    students = db.query(User).filter(User.role == "student").order_by(User.email).all()
    result = []
    for student in students:
        progress = db.query(Progress).filter(Progress.user_id == student.id).first()
        result.append(
            {
                "id": student.id,
                "email": student.email,
                "nom": student.nom,
                "niveau_cecrl": student.niveau_cecrl,
                "conversations_completees": progress.conversations_completees if progress else 0,
                "points": progress.points if progress else 0,
            }
        )
    return result


@router.get("/students/{student_id}/dashboard")
def get_student_dashboard(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tableau de bord complet d'un élève précis (mêmes données que /progress/{id}/dashboard)."""
    _require_teacher(current_user)

    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    progress = db.query(Progress).filter(Progress.user_id == student_id).first()
    if not progress:
        return {
            "user_id": student_id,
            "email": student.email,
            "niveau_estime": student.niveau_cecrl,
            "conversations_completees": 0,
            "erreurs_frequentes": [],
            "niveau_historique": [],
            "erreurs_par_semaine": [],
            "badges": [],
        }

    stats = conversation_service.get_progression_stats(db, student_id)
    return {
        "user_id": student_id,
        "email": student.email,
        "niveau_estime": progress.niveau_estime,
        "conversations_completees": progress.conversations_completees,
        "points": progress.points,
        "badges": conversation_service.compute_badges(progress),
        **stats,
    }
