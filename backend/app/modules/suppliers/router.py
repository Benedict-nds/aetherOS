from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, ROLE_PHARMACIST, ROLE_STAFF, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.audit.service import resolve_client_ip
from app.modules.suppliers.schemas import SupplierCreate, SupplierUpdate
from app.modules.suppliers.service import create_supplier_record, deactivate_supplier_record, get_supplier_record, list_supplier_records, update_supplier_record

router = APIRouter()
read_suppliers = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF)
manage_suppliers = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST)


@router.get("")
def list_suppliers(q: str | None = None, is_active: bool | None = None,
                  limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0),
                  current_user: User = Depends(read_suppliers), db: Session = Depends(get_db)):
    data = list_supplier_records(db, q=q, is_active=is_active, limit=limit, offset=offset)
    return success_response(data=data, message="Suppliers retrieved")


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int, current_user: User = Depends(read_suppliers), db: Session = Depends(get_db)):
    supplier = get_supplier_record(db, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return success_response(data=supplier, message="Supplier retrieved")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, request: Request, current_user: User = Depends(manage_suppliers), db: Session = Depends(get_db)):
    data = create_supplier_record(db, current_user, payload, ip_address=resolve_client_ip(request))
    return success_response(data=data, message="Supplier created")


@router.patch("/{supplier_id}")
def update_supplier(supplier_id: int, payload: SupplierUpdate, request: Request, current_user: User = Depends(manage_suppliers), db: Session = Depends(get_db)):
    data = update_supplier_record(db, current_user, supplier_id, payload, ip_address=resolve_client_ip(request))
    return success_response(data=data, message="Supplier updated")


@router.delete("/{supplier_id}")
def deactivate_supplier(supplier_id: int, request: Request, current_user: User = Depends(manage_suppliers), db: Session = Depends(get_db)):
    deactivate_supplier_record(db, current_user, supplier_id, ip_address=resolve_client_ip(request))
    return success_response(data=None, message="Supplier deactivated")
