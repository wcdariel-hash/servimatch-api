from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from passlib.context import CryptContext
import os
import random

router = APIRouter(prefix="/api/admin", tags=["Admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/seed")
def seed_database(x_admin_secret: str = Header(None), db: Session = Depends(get_db)):
    # Simple security check using an environment variable
    expected_secret = os.getenv("SEED_SECRET", "super-secret-servimatch-key-2026")
    if x_admin_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    # 1. Clean existing data (Optional: user might want to keep data, but for first seed it's better to clean)
    db.query(models.Booking).delete()
    db.query(models.Message).delete()
    db.query(models.ServiceModel).delete()
    db.query(models.User).delete()
    db.commit()

    # 2. Create Test Users
    test_user = models.User(
        email="test@email.com",
        full_name="Usuario de Prueba",
        hashed_password=get_password_hash("dcastillo2009"),
        balance=500.0,
        is_verified=True,
        is_phone_verified=True,
        phone_number="+18091234567"
    )
    
    provider_user = models.User(
        email="provider@email.com",
        full_name="Profesional ServiMatch",
        hashed_password=get_password_hash("dcastillo2009"),
        balance=50.0,
        is_provider=True,
        is_verified=True,
        is_phone_verified=True
    )
    
    db.add(test_user)
    db.add(provider_user)
    db.commit()
    db.refresh(test_user)
    db.refresh(provider_user)

    # 3. Create Services
    LAT_BASE = 18.4861
    LNG_BASE = -69.9312

    services_data = [
        {"title": "Limpieza de Hogar Express", "p": "Ana Martínez", "d": "Limpieza profunda con desinfección total.", "pr": 25.0, "c": "Hogar", "i": "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=800"},
        {"title": "Gasfitería & Plomería 24/7", "p": "Pedro Font", "d": "Reparación de filtraciones y tuberías.", "pr": 35.0, "c": "Hogar", "i": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800"},
        {"title": "Soporte Técnico Laptop", "p": "Tech Solutions", "d": "Formateo y cambio de discos SSD.", "pr": 45.0, "c": "Tecnología", "i": "https://images.unsplash.com/photo-1591799264318-7e6ef8ddb7ea?w=800"},
        {"title": "Barbería Premium", "p": "Carlos Cuts", "d": "Corte de cabello y barba moderno.", "pr": 15.0, "c": "Salud", "i": "https://images.unsplash.com/photo-1503951914875-452162b0f3f1?w=800"},
        {"title": "Clases de Matemáticas", "p": "Prof. Roberto", "d": "Álgebra y Cálculo universitario.", "pr": 20.0, "c": "Educación", "i": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800"},
        {"title": "Electricista Matriculado", "p": "Juan Voltio", "d": "Instalaciones eléctricas y tableros.", "pr": 40.0, "c": "Hogar", "i": "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800"}
    ]

    for s in services_data:
        lat_off = (random.random() - 0.5) * 0.05
        lng_off = (random.random() - 0.5) * 0.05
        
        service = models.ServiceModel(
            title=s["title"],
            provider_name=s["p"],
            description=s["d"],
            price=s["pr"],
            category=s["c"],
            image_url=s["i"],
            latitude=LAT_BASE + lat_off,
            longitude=LNG_BASE + lng_off,
            payment_methods="ServiPay, Efectivo",
            owner_id=provider_user.id
        )
        db.add(service)

    db.commit()
    return {"message": "Database seeded successfully", "users": 2, "services": len(services_data)}
