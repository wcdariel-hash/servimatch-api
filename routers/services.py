from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List, Optional
from geopy.distance import geodesic

router = APIRouter(prefix="/api/services", tags=["Services"])

@router.get("/", response_model=List[schemas.Service])
def get_services(
    search: Optional[str] = None,
    category: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.ServiceModel).filter(models.ServiceModel.is_active == True)

    if category and category != "Todos":
        query = query.filter(models.ServiceModel.category == category)
    
    if search:
        query = query.filter(
            (models.ServiceModel.title.ilike(f"%{search}%")) | 
            (models.ServiceModel.description.ilike(f"%{search}%"))
        )

    services = query.all()

    # Si se pasan coordenadas, ordenar por cercanía
    if lat is not None and lng is not None:
        user_coords = (lat, lng)
        for s in services:
            if s.latitude and s.longitude:
                service_coords = (s.latitude, s.longitude)
                s.distance = round(geodesic(user_coords, service_coords).km, 1)
            else:
                s.distance = 999.0 # Muy lejos si no tiene GPS
        
        services.sort(key=lambda x: getattr(x, 'distance', 999.0))

    return services

@router.post("/", response_model=schemas.Service)
def create_service(service: schemas.ServiceCreate, db: Session = Depends(get_db)):
    db_service = models.ServiceModel(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/{service_id}", response_model=schemas.Service)
def get_service(service_id: int, db: Session = Depends(get_db)):
    service = db.query(models.ServiceModel).filter(models.ServiceModel.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return service
