
import asyncio
from unittest.mock import AsyncMock

from game.backend.connection_manager import ConnectionManager


def test_connection_lifecycle():
    manager = ConnectionManager()

    class FakeWebSocket:
        def __init__(self):
            self.accept = AsyncMock()

    ws = FakeWebSocket()

    # Initially unregistered
    assert manager.get_identity(ws) is None

    # Connect
    asyncio.run(manager.connect(ws, "table1", 0))

    ws.accept.assert_awaited_once()
    assert manager.get_identity(ws) == ("table1", 0)

    # Disconnect
    manager.disconnect(ws)

    assert manager.get_identity(ws) is None

    # Repeated disconnect should be harmless
    manager.disconnect(ws)
