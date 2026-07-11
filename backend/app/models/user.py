from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    niveau_cecrl = Column(String, default="A1")
    # Re-added by migration 0004: had been dropped by 9a9611e31c70 even
    # though auth.py, deps.py and UserOut all still rely on it.
    is_active = Column(Boolean, default=True, nullable=False)
    # --- Phase 7 : mode enseignant ---
    # "student" (défaut) ou "teacher". Un compte "teacher" peut consulter
    # le tableau de bord de n'importe quel élève via /teacher/students.
    role = Column(String, default="student", nullable=False)
    # --- Phase 8 : scaffold freemium/premium ---
    # "free" (défaut) ou "premium". Utilisé pour moduler les limites de
    # débit (rate limiting) ; l'intégration d'un vrai moyen de paiement
    # (Stripe ou autre) reste à brancher séparément, cf. README.
    plan = Column(String, default="free", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
