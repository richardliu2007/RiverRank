import asyncio
from game.backend.snapshot_manager import SnapshotManager

def test_mailbox():
    async def run():
        mailbox = SnapshotManager()

        mailbox.publish({"version": 10})
        mailbox.publish({"version": 11})
        mailbox.publish({"version": 12})

        result = await asyncio.wait_for(mailbox.receive(), timeout=1)

        assert result["version"] == 12
        assert mailbox.queue.empty()

    asyncio.run(run())
