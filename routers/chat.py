from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import json
from database import get_db
import models, schemas
from routers.auth import get_current_user_from_token, get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Manager de Conexiones Activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    user = get_current_user_from_token(token, db)
    if user is None:
        await websocket.close(code=4001)
        return

    await manager.connect(user.id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Guardar en DB
            db_message = models.Message(
                sender_id=user.id,
                receiver_id=message_data['receiver_id'],
                content=message_data['content']
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            # Reenviar al receptor si está conectado
            response_data = {
                "id": db_message.id,
                "sender_id": db_message.sender_id,
                "receiver_id": db_message.receiver_id,
                "content": db_message.content,
                "timestamp": db_message.timestamp.isoformat(),
                "is_read": db_message.is_read
            }
            await manager.send_personal_message(json.dumps(response_data), message_data['receiver_id'])
            
    except WebSocketDisconnect:
        manager.disconnect(user.id)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(user.id)

@router.get("/history/{other_user_id}", response_model=List[schemas.MessageResponse])
def get_chat_history(other_user_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    messages = db.query(models.Message).filter(
        ((models.Message.sender_id == current_user.id) & (models.Message.receiver_id == other_user_id)) |
        ((models.Message.sender_id == other_user_id) & (models.Message.receiver_id == current_user.id))
    ).order_by(models.Message.timestamp.asc()).all()
    return messages
