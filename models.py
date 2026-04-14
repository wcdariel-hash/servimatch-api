from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_provider = Column(Boolean, default=False)
    
    # Seguridad Bancaria (Email)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    otp_expires = Column(DateTime, nullable=True)
    
    # Seguridad Bancaria (Teléfono)
    is_phone_verified = Column(Boolean, default=False)
    phone_otp_code = Column(String, nullable=True)
    phone_otp_expires = Column(DateTime, nullable=True)
    
    # ServiPay Wallet
    balance = Column(Float, default=0.0)
    reserved_balance = Column(Float, default=0.0)
    
    # Ubicación (Seguimiento Real)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    services = relationship("ServiceModel", back_populates="owner")
    bookings = relationship("Booking", back_populates="user")

class ServiceModel(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    provider_name = Column(String)
    description = Column(String)
    price = Column(Float)
    is_active = Column(Boolean, default=True)
    category = Column(String, default="General")
    payment_methods = Column(String, default="Efectivo")
    image_url = Column(String, nullable=True) # Para fotos de catálogo
    
    # Coordenadas del Servicio
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    owner = relationship("User", back_populates="services")
    bookings = relationship("Booking", back_populates="service")

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    price = Column(Float)
    payment_method = Column(String) # "Efectivo", "Tarjeta", "ServiPay"
    status = Column(String, default="Completado")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="bookings")
    service = relationship("ServiceModel", back_populates="bookings")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])

class LoginAudit(Base):
    __tablename__ = "login_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    status = Column(String) # "SUCCESS", "FAIL", "ABORTED"
    reason = Column(String, nullable=True) # "Incorrect Password", "User Not Found", etc.
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True) # Para saber si es Opera, Chrome, etc.
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
