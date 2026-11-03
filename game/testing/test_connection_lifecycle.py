
from fastapi.testclient import TestClient

from game.backend.app import app, manager


def test_normal_disconnect_cleans_up_tasks():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/demo") as websocket:
            welcome = websocket.receive_json()

            assert welcome["type"] == "welcome"
            assert len(manager.connections) == 1

            connection = next(iter(manager.connections.values()))
            sender_task = connection.sender_task

            assert not sender_task.done()

        # WebSocket context has now exited.
        assert len(manager.connections) == 0
        assert sender_task.done()
