from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional
import random
import string

from database import get_db
import models
import schemas
from mail_service import send_otp_email
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import requests
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "981190772478-e0222kqd2qpfhq255o1enio18dnt9fjv.apps.googleusercontent.com")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def record_login_attempt(db: Session, email: str, status: str, reason: str = None, request: Request = None):
    audit = models.LoginAudit(
        email=email,
        status=status,
        reason=reason,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit)
    db.commit()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_token(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        user = db.query(models.User).filter(models.User.email == email).first()
        return user
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = get_current_user_from_token(token, db)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    db_phone = db.query(models.User).filter(models.User.phone_number == user.phone_number).first()
    if db_phone:
        raise HTTPException(status_code=400, detail="El número de teléfono ya está registrado")
    
    hashed_password = get_password_hash(user.password)
    
    # Generar OTP de 6 dígitos (Email)
    email_otp = ''.join(random.choices(string.digits, k=6))
    email_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    
    # Generar OTP de 6 dígitos (Phone)
    phone_otp = ''.join(random.choices(string.digits, k=6))
    phone_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    
    new_user = models.User(
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name, 
        hashed_password=hashed_password, 
        is_provider=True,
        is_verified=False,
        otp_code=email_otp,
        otp_expires=email_otp_expires,
        is_phone_verified=False,
        phone_otp_code=phone_otp,
        phone_otp_expires=phone_otp_expires,
        balance=100.0 # Bono de bienvenida para probar ServiPay
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Enviar correo real (Background Task)
    background_tasks.add_task(send_otp_email, user.email, email_otp)
    
    # Simulación de SMS (Consola)
    print(f"[SMS SIMULATION] Para: {user.phone_number} -> OTP: {phone_otp}\n")
    
    return new_user

@router.post("/verify-email")
def verify_email(email: str, code: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.is_verified:
        return {"message": "La cuenta ya está verificada"}
    
    if user.otp_code != code:
        raise HTTPException(status_code=400, detail="Código OTP incorrecto")
    
    if datetime.utcnow() > user.otp_expires:
        raise HTTPException(status_code=400, detail="El código OTP ha expirado")
    
    user.is_verified = True
    user.otp_code = None
    user.otp_expires = None
    db.commit()
    
    return {"message": "Email verificado exitosamente"}

@router.post("/verify-phone")
def verify_phone(email: str, code: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.is_phone_verified:
        return {"message": "El teléfono ya está verificado"}
    
    if user.phone_otp_code != code:
        raise HTTPException(status_code=400, detail="Código SMS incorrecto")
    
    if datetime.utcnow() > user.phone_otp_expires:
        raise HTTPException(status_code=400, detail="El código SMS ha expirado")
    
    user.is_phone_verified = True
    user.phone_otp_code = None
    user.phone_otp_expires = None
    db.commit()
    
    return {"message": "Teléfono verificado exitosamente"}

@router.post("/login", response_model=schemas.Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user:
        record_login_attempt(db, form_data.username, "FAIL", "Usuario no encontrado", request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        record_login_attempt(db, form_data.username, "FAIL", "Contraseña incorrecta", request)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Éxito
    record_login_attempt(db, user.email, "SUCCESS", None, request)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/resend-email")
def resend_email(email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Generar nuevo OTP
    new_otp = ''.join(random.choices(string.digits, k=6))
    user.otp_code = new_otp
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    background_tasks.add_task(send_otp_email, email, new_otp)
    return {"message": "Nuevo código enviado"}

@router.post("/resend-phone")
def resend_phone(email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Generar nuevo OTP para teléfono
    new_otp = ''.join(random.choices(string.digits, k=6))
    user.phone_otp_code = new_otp
    user.phone_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    
    # Simulación de SMS (Consola)
    print(f"[SMS RESEND SIMULATION] Para: {user.phone_number} -> OTP: {new_otp}")
    return {"message": "Nuevo código SMS enviado"}

@router.post("/google")
def google_auth(google_token: str, db: Session = Depends(get_db)):
    try:
        # Verificar el token con Google
        idinfo = id_token.verify_oauth2_token(google_token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID de usuario único de Google
        # userid = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', 'Usuario de Google')

        # Buscar usuario en DB
        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            # Registrar automáticamente si no existe
            user = models.User(
                email=email,
                full_name=name,
                phone_number=f"GOOGLE_{email[:10]}", # Placeholder ya que no tenemos el tlf de Google
                hashed_password="SOCIAL_AUTH_G",
                is_verified=True, # Google ya verificó el email
                is_phone_verified=True,
                balance=100.0
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generar JWT de ServiMatch
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except ValueError as e:
        # Token inválido
        record_login_attempt(db, "unknown_google", "FAIL", f"Token Google Inválido: {str(e)}")
        raise HTTPException(status_code=400, detail="Token de Google inválido")
    except Exception as e:
        record_login_attempt(db, "google_error", "ABORTED", str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user
