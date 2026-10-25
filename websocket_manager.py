from fastapi import WebSocket

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        if user_id in self.active_connections:
            self.active_connections[user_id].append(websocket)
        else:
            self.active_connections[user_id] = [websocket]

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        if user_id not in self.active_connections:
            return

        if websocket in self.active_connections[user_id]:
            self.active_connections[user_id].remove(websocket)
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]

    async def send_personal_message(self, data: dict, user_id: int) -> None:
        if user_id not in self.active_connections:
            return

        for websocket in self.active_connections[user_id]:
            await websocket.send_json(data)

manager = ConnectionManager()