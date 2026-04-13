from database import SessionLocal
import models

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == "test@email.com").first()
if user:
    print(f"User found: {user.email}")
    print(f"Hashed Password: {user.hashed_password}")
else:
    print("User not found")
db.close()
