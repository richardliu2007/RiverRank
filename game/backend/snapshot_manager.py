import asyncio

class SnapshotManager:
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=1)

    def publish(self, snapshot: dict) -> None:
        # Discard stale snapshots
        if self.queue.full():
            self.queue.get_nowait()
        self.queue.put_nowait(snapshot)

    async def receive(self) -> dict:
        # Wait asynchronously for the next
        # available snapshot.
        return await self.queue.get()