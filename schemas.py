from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ----- Auth & Usuarios -----
class UserCreate(BaseModel):
    email: EmailStr
    phone_number: str
    full_name: str
    password: str

class UserLogin(BaseModel) :
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    phone_number: Optional[str]
    full_name: str
    is_provider: bool
    is_verified: bool
    is_phone_verified: bool
    balance: float
    reserved_balance: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# ----- Servicios -----
class ServiceCreate(BaseModel):
    title: str
    provider_name: str
    description: str
    price: float
    category: Optional[str] = "General"
    payment_methods: Optional[str] = "Efectivo"
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Service(BaseModel):
    id: int
    title: str
    provider_name: str
    description: str
    price: float
    is_active: bool
    owner_id: Optional[int] = None
    category: Optional[str] = "General"
    payment_methods: Optional[str] = "Efectivo"
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance: Optional[float] = None 

    class Config:
        from_attributes = True

# ----- Reservas (Bookings) -----
class BookingCreate(BaseModel):
    service_id: int
    payment_method: str

class BookingResponse(BaseModel):
    id: int
    user_id: int
    service_id: int
    price: float
    payment_method: str
    status: str
    created_at: datetime
    service: Service
    user: UserResponse

    class Config:
        from_attributes = True

# ----- Mensajes (Chat) -----
class MessageCreate(BaseModel):
    receiver_id: int
    content: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    timestamp: datetime
    is_read: bool

    class Config:
        from_attributes = True
