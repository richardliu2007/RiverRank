from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[
            WebSocket, tuple[str, int]
        ] = {}

    async def connect(
        self,
        websocket: WebSocket,
        table_id: str,
        seat_id: int
    ):
        await websocket.accept()
        self.connections[websocket] = (table_id, seat_id)

    def disconnect(self, websocket: WebSocket):
        self.connections.pop(websocket, None)

    def get_identity(
        self, websocket: WebSocket
    ) -> tuple[str, int] | None:
        return self.connections.get(websocket)