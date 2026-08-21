"""Operations API routes: events, exceptions, orders, forklifts, suppliers."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import (
    CustomerOrder,
    Exception_,
    Forklift,
    OperationalEvent,
    Supplier,
)
from app.schemas.schemas import (
    CustomerOrderOut,
    ExceptionOut,
    ForkliftOut,
    OperationalEventOut,
    SupplierOut,
)

router = APIRouter(tags=["operations"])


@router.get("/events", response_model=list[OperationalEventOut])
def list_events(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(OperationalEvent)
        .order_by(OperationalEvent.timestamp.desc())
        .limit(limit)
        .all()
    )


@router.get("/exceptions", response_model=list[ExceptionOut])
def list_exceptions(resolved: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(Exception_)
    if resolved is not None:
        q = q.filter(Exception_.resolved == resolved)
    return q.order_by(Exception_.severity.desc(), Exception_.created_at.desc()).all()


@router.get("/orders", response_model=list[CustomerOrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.query(CustomerOrder).order_by(CustomerOrder.code).all()


@router.get("/forklifts", response_model=list[ForkliftOut])
def list_forklifts(db: Session = Depends(get_db)):
    return db.query(Forklift).order_by(Forklift.code).all()


@router.get("/suppliers", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).order_by(Supplier.code).all()
