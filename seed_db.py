from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import random
from passlib.context import CryptContext

# Configuración de hashing (debe coincidir con auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# Asegurar que las tablas existan con las nuevas columnas
models.Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # Comprobar si ya existe el usuario maestro para asegurar usuario maestro
    existing_user = db.query(models.User).filter(models.User.email == "test@email.com").first()
    if existing_user:
        print("Sincronizando contraseñas del usuario maestro...")
        existing_user.hashed_password = get_password_hash("dcastillo2009")
        db.commit()
        db.close()
        return

    print("Iniciando poblado de base de datos (Primera vez)...")

    # 2. Crear Usuarios de Prueba
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

    # Coordenadas base: Santo Domingo, RD (Centro)
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
            owner_id=provider_user.id # Asignar al proveedor creado
        )
        db.add(service)

    db.commit()
    print(f"Poblado completado: {len(services_data)} servicios y 2 usuarios creados.")
    db.close()

if __name__ == "__main__":
    seed()
