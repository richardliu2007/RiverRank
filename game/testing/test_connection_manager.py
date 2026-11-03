import asyncio
from unittest.mock import AsyncMock

from game.backend.connection_manager import ConnectionManager


def test_connection_lifecycle():
    class FakeWebSocket:
        def __init__(self):
            self.accept = AsyncMock()
            self.sent = asyncio.Event()
            self.send_json = AsyncMock(side_effect=self.mark_sent)

        async def mark_sent(self, message):
            self.sent.set()

    async def run():
        manager = ConnectionManager()
        ws = FakeWebSocket()
        welcome = {"type": "welcome", "seat_id": 0}

        assert manager.get_identity(ws) is None

        await manager.accept(ws)
        ws.accept.assert_awaited_once()
        assert manager.get_identity(ws) is None

        manager.register(ws, "table1", 0, welcome)
        sender_task = manager.connections[ws].sender_task
        try:
            assert manager.get_identity(ws) == ("table1", 0)
            assert manager.get_table_connections("table1") == [(ws, 0)]
            await asyncio.wait_for(ws.sent.wait(), timeout=1)
            ws.send_json.assert_awaited_once_with(welcome)
            assert not sender_task.done()
        finally:
            await manager.disconnect(ws)

        assert manager.get_identity(ws) is None
        assert manager.get_table_connections("table1") == []
        assert sender_task.cancelled()

        # Repeated disconnect should be harmless.
        await manager.disconnect(ws)

    asyncio.run(run())
