from fastapi import WebSocket
from dataclasses import dataclass
import asyncio
from game.backend.outbox import Outbox

@dataclass
class ConnectionState:
    table_id: str
    seat_id: int
    outbox: Outbox
    sender_task: asyncio.Task

class ConnectionManager:
    def __init__(self):
        self.connections: dict[
            WebSocket, ConnectionState
        ] = {}

    async def accept(self, websocket):
        await websocket.accept()

    def register(self, websocket, table_id, seat_id, welcome):
        if websocket in self.connections:
            raise ValueError("WebSocket already registered")
        outbox = Outbox()
        outbox.publish_control(welcome)

        sender_task = asyncio.create_task(
            self.sender_loop(websocket, outbox)
        )
        self.connections[websocket] = ConnectionState(table_id, seat_id, outbox, sender_task)
    

    async def disconnect(self, websocket: WebSocket) -> None:
        connection = self.connections.pop(websocket, None)

        if connection is None:
            return

        task = connection.sender_task
        task.cancel()

        await asyncio.gather(
            task,
            return_exceptions=True,
        )

            

    
    async def sender_loop(
        self,
        websocket: WebSocket,
        outbox: Outbox,
    ) -> None:
        while True:
            message = await outbox.receive()
            await websocket.send_json(message)

    def get_identity(
        self,
        websocket: WebSocket,
    ) -> tuple[str, int] | None:
        connection = self.connections.get(websocket)

        if connection is None:
            return None

        return connection.table_id, connection.seat_id


    def get_table_connections(
        self,
        table_id: str,
    ) -> list[tuple[WebSocket, int]]:
        return [
            (websocket, connection.seat_id)
            for websocket, connection in self.connections.items()
            if connection.table_id == table_id
        ]
