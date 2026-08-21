"""Inventory-related API routes: pallets, inventory items."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.models import InventoryItem, Pallet
from app.schemas.schemas import InventoryItemOut, PalletOut

router = APIRouter(tags=["inventory"])


@router.get("/pallets", response_model=list[PalletOut])
def list_pallets(db: Session = Depends(get_db)):
    pallets = db.query(Pallet).options(joinedload(Pallet.bay)).all()
    results = []
    for p in pallets:
        out = PalletOut.model_validate(p)
        out.bay_code = p.bay.code if p.bay else None
        results.append(out)
    return results


@router.get("/inventory", response_model=list[InventoryItemOut])
def list_inventory(
    stock_status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(InventoryItem)
    if stock_status:
        q = q.filter(InventoryItem.stock_status == stock_status)
    return q.order_by(InventoryItem.sku).all()
