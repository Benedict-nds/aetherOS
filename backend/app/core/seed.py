from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.medicine import Medicine
from app.models.medicine_category import MedicineCategory
from app.models.role import Role
from app.models.user import User
from app.modules.auth.repository import get_user_by_email


def seed_demo_user(db: Session) -> None:
    if get_user_by_email(db, settings.demo_email) is not None:
        return

    role = db.scalar(
        select(Role).where(Role.name == settings.demo_role)
    )

    if role is None:
        raise RuntimeError(
            f"Role '{settings.demo_role}' not found; run migrations first"
        )

    db.add(
        User(
            full_name=settings.demo_full_name,
            email=settings.demo_email,
            username=settings.demo_username,
            password_hash=hash_password(settings.demo_password),
            role_id=role.id,
            status="active",
        )
    )
    db.commit()


def seed_inventory_catalogue(db: Session) -> None:
    existing = db.scalar(select(MedicineCategory).limit(1))
    if existing is not None:
        return

    categories = {
        "Antibiotics": MedicineCategory(
            name="Antibiotics",
            description="Antibacterial medicines",
            status="active",
        ),
        "Cardiovascular": MedicineCategory(
            name="Cardiovascular",
            description="Heart and blood pressure medicines",
            status="active",
        ),
        "Antidiabetic": MedicineCategory(
            name="Antidiabetic",
            description="Diabetes management medicines",
            status="active",
        ),
    }
    db.add_all(categories.values())
    db.flush()

    seed_medicines = [
        Medicine(
            name="Amoxicillin 500mg Capsule",
            generic_name="Amoxicillin",
            brand_name="Amoxil",
            category_id=categories["Antibiotics"].id,
            barcode="AMOX500001",
            dosage_form="Capsule",
            strength="500",
            unit="mg",
            reorder_level=20,
            is_active=True,
        ),
        Medicine(
            name="Metformin 500mg Tablet",
            generic_name="Metformin",
            brand_name="Glucophage",
            category_id=categories["Antidiabetic"].id,
            barcode="MET500001",
            dosage_form="Tablet",
            strength="500",
            unit="mg",
            reorder_level=30,
            is_active=True,
        ),
        Medicine(
            name="Lisinopril 10mg Tablet",
            generic_name="Lisinopril",
            brand_name="Zestril",
            category_id=categories["Cardiovascular"].id,
            barcode="LIS10001",
            dosage_form="Tablet",
            strength="10",
            unit="mg",
            reorder_level=15,
            is_active=True,
        ),
        Medicine(
            name="Atorvastatin 20mg Tablet",
            generic_name="Atorvastatin",
            brand_name="Lipitor",
            category_id=categories["Cardiovascular"].id,
            barcode="ATO20001",
            dosage_form="Tablet",
            strength="20",
            unit="mg",
            reorder_level=25,
            is_active=True,
        ),
        Medicine(
            name="Paracetamol 500mg Tablet",
            generic_name="Paracetamol",
            brand_name="Panadol",
            category_id=None,
            barcode="PARA500001",
            dosage_form="Tablet",
            strength="500",
            unit="mg",
            reorder_level=50,
            is_active=True,
        ),
        Medicine(
            name="Omeprazole 20mg Capsule",
            generic_name="Omeprazole",
            brand_name="Losec",
            category_id=categories["Antibiotics"].id,
            barcode="OMP20001",
            dosage_form="Capsule",
            strength="20",
            unit="mg",
            reorder_level=10,
            is_active=True,
        ),
    ]
    db.add_all(seed_medicines)
    db.commit()
