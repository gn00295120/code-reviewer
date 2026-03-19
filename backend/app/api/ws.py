from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.websocket import ws_manager

router = APIRouter()


@router.websocket("/ws/reviews/{review_id}")
async def review_websocket(websocket: WebSocket, review_id: str):
    room = f"review:{review_id}"
    await ws_manager.connect(websocket, room)
    try:
        while True:
            # Keep connection alive, handle client messages if needed
            data = await websocket.receive_text()
            # Client can send ping/pong or commands here
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, room)
