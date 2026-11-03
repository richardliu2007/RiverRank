
import asyncio
from collections import deque


class Outbox:
    def __init__(self):
        self.controls = deque()
        self.latest_snapshot = None
        self.ready = asyncio.Event()

    def publish_control(self, message: dict):
        # Append control message in FIFO order
        # Signal that new work is available
        self.controls.append(message)
        self.ready.set()

    def publish_snapshot(self, snapshot: dict):
        # Replace the previous pending snapshot
        # Signal that new work is available
        self.latest_snapshot = snapshot
        self.ready.set()

    
    async def receive(self) -> dict:
        while True:
            if self.controls:
                message = self.controls.popleft()

            elif self.latest_snapshot is not None:
                message = self.latest_snapshot
                self.latest_snapshot = None

            else:
                self.ready.clear()
                await self.ready.wait()
                continue

            if not self.controls and self.latest_snapshot is None:
                self.ready.clear()

            return message


