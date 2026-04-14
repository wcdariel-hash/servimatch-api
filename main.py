from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routers import auth, services, bookings, chat, admin
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Configuración del Limiter (Anti-Fuerza Bruta)
limiter = Limiter(key_func=get_remote_address)

# Crear tablas de base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ServiMatch API Premium")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware de Seguridad Máxima
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self' https:; script-src 'self' 'unsafe-inline' https:; style-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:; connect-src 'self' https: ws:;"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Configurar CORS para Flutter Web
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "https://servimatch-api.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(chat.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a ServiMatch API Premium", "v": "1.0.4"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
