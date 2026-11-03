from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from game.backend.connection_manager import ConnectionManager
from game.backend.seat_registry import SeatRegistry
from game.backend.game_session import GameSession
from game.game_engine import Game, Player
from game.backend.protocol import (
    parse_action_message,
    ProtocolError,
)
import logging
import json

logger = logging.getLogger(__name__)

import asyncio

table_lock = asyncio.Lock()

app = FastAPI()

players = [Player("Alice"), Player("Bob")]
game = Game(0, 1, 1, players, 2000)
game._startHand()

manager = ConnectionManager()
seats = SeatRegistry(max_seats=2)
session = GameSession(game)

async def receive_actions(
    websocket: WebSocket,
    table_id: str,
) -> None:
    while True:
        try:
            msg = await websocket.receive_json()

        except json.JSONDecodeError:
            connection = manager.connections.get(websocket)

            if connection is None:
                return

            connection.outbox.publish_control({
                "type": "error",
                "error": "malformed JSON",
            })
            continue

        try:
            action = parse_action_message(msg)

        except ProtocolError:
            connection = manager.connections.get(websocket)

            if connection is None:
                return

            connection.outbox.publish_control({
                "type": "error",
                "error": "invalid message",
            })
            continue

        async with table_lock:
            identity = manager.get_identity(websocket)
            if identity is None:
                break

            player = session.game.players[identity[1]]
            valid = session.submit_action(player, action)

            if valid:
                version = session.version

                for recipient, seat in manager.get_table_connections(table_id):
                    connection = manager.connections[recipient]

                    state = session.game.getVisibleState(
                        session.game.players[seat]
                    )

                    connection.outbox.publish_snapshot({
                        "type": "snapshot",
                        "version": version,
                        "state": state,
                    })
            else:
                connection = manager.connections[websocket]

                connection.outbox.publish_control({
                    "type": "error",
                    "error": "invalid action",
                })

async def supervise_tasks(
    receiver_task: asyncio.Task,
    sender_task: asyncio.Task,
) -> None:
    try:
        done, _ = await asyncio.wait(
            {receiver_task, sender_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in done:
            if task.cancelled():
                continue

            error = task.exception()
            if error is not None and not isinstance(
                error, WebSocketDisconnect
            ):
                logger.error(
                    "Connection task failed",
                    exc_info=(
                        type(error),
                        error,
                        error.__traceback__,
                    ),
                )
    finally:
        receiver_task.cancel()
        await asyncio.gather(
            receiver_task,
            return_exceptions=True,
        )


@app.websocket("/ws/{table_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    table_id: str,
):
    if table_id != "demo":
        await websocket.close(code=1008)
        return
    established = False
    seat_id = seats.reserve_seat()
    if seat_id is None:
        await websocket.close(code=1008)
        return
    try:
        await manager.accept(websocket)
        async with table_lock:
            player = session.game.players[seat_id]
            welcome = {
                "type": "welcome",
                "seat_id": seat_id,
                "state": session.game.getVisibleState(player),
                "version": session.version,
            }
            manager.register(
                websocket, table_id, seat_id, welcome
            )
        established = True

        
        receiver_task = asyncio.create_task(
            receive_actions(websocket, table_id)
        )

        sender_task = manager.connections[websocket].sender_task

        await supervise_tasks(receiver_task, sender_task)


    finally:
        await manager.disconnect(websocket)
        if not established:
            seats.release_seat(seat_id)
