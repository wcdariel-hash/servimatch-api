from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(
    prefix="/api/bookings",
    tags=["bookings"]
)

@router.post("/", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # 1. Buscar el servicio
    db_service = db.query(models.ServiceModel).filter(models.ServiceModel.id == booking.service_id).first()
    if not db_service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    
    provider = db.query(models.User).filter(models.User.id == db_service.owner_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    # 2. Lógica ServiPay (Billetera)
    if booking.payment_method == "ServiPay":
        if current_user.balance < db_service.price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Saldo insuficiente en ServiPay. Tienes ${current_user.balance} y necesitas ${db_service.price}"
            )
        # Descontar del wallet del cliente
        current_user.balance -= db_service.price
        # Añadir al saldo reservado del proveedor
        provider.reserved_balance += db_service.price
    
    # 3. Crear el registro de la reserva (Pendiente)
    db_booking = models.Booking(
        user_id=current_user.id,
        service_id=db_service.id,
        price=db_service.price,
        payment_method=booking.payment_method,
        status="Pendiente"
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    return db_booking

@router.post("/{booking_id}/complete", response_model=schemas.BookingResponse)
def complete_booking(booking_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_booking = db.query(models.Booking).options(joinedload(models.Booking.service)).filter(models.Booking.id == booking_id).first()
    
    if not db_booking:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        
    if db_booking.service.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para completar este trabajo")
        
    if db_booking.status == "Completado":
        raise HTTPException(status_code=400, detail="Este trabajo ya está completado")
        
    db_booking.status = "Completado"
    
    # Transferir fondos si fue por ServiPay
    if db_booking.payment_method == "ServiPay":
        current_user.reserved_balance -= db_booking.price
        current_user.balance += db_booking.price
        
    db.commit()
    db.refresh(db_booking)
    return db_booking

@router.get("/my-purchases", response_model=List[schemas.BookingResponse])
def get_my_purchases(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Booking).options(joinedload(models.Booking.user), joinedload(models.Booking.service)).filter(models.Booking.user_id == current_user.id).all()

@router.get("/my-jobs", response_model=List[schemas.BookingResponse])
def get_my_jobs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Buscar servicios que pertenecen al usuario actual y obtener al cliente
    return db.query(models.Booking).join(models.ServiceModel).options(joinedload(models.Booking.user), joinedload(models.Booking.service)).filter(models.ServiceModel.owner_id == current_user.id).all()

# Endpoint para recargar saldo (Simulado para testing como pidió el usuario)
@router.post("/wallet/add")
def add_balance(amount: float, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Monto debe ser mayor a 0")
    
    current_user.balance += amount
    db.commit()
    return {"message": f"Se han añadido ${amount} a tu cuenta", "new_balance": current_user.balance}
