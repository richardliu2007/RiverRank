
import asyncio

import pytest

from game.backend.connection_manager import ConnectionManager


class FailingWebSocket:
    async def send_json(self, message):
        raise OSError("Simulated connection failure")


def test_sender_failure_cleanup():

    async def run():
        manager = ConnectionManager()
        websocket = FailingWebSocket()

        manager.register(
            websocket,
            "demo",
            0,
            {"type": "welcome", "seat_id": 0},
        )

        task = manager.connections[websocket].sender_task

        # The sender should fail while sending welcome.
        with pytest.raises(OSError):
            await asyncio.wait_for(task, timeout=1)

        assert task.done()

        # Cleanup must succeed despite the failed sender.
        await manager.disconnect(websocket)

        assert websocket not in manager.connections

        print("Sender failure cleanup passed!")

    asyncio.run(run())
