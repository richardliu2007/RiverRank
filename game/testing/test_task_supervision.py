
import asyncio

from game.backend.app import supervise_tasks


def test_sender_failure_cancels_receiver():
    async def run():
        receiver_terminated = asyncio.Event()

        async def receiver():
            try:
                await asyncio.Event().wait()
            finally:
                receiver_terminated.set()

        async def sender():
            await asyncio.sleep(0)
            raise OSError("Simulated network failure")

        receiver_task = asyncio.create_task(receiver())
        sender_task = asyncio.create_task(sender())

        await asyncio.wait_for(
            supervise_tasks(receiver_task, sender_task),
            timeout=2,
        )

        assert sender_task.done()
        assert isinstance(sender_task.exception(), OSError)

        assert receiver_task.done()
        assert receiver_task.cancelled()
        assert receiver_terminated.is_set()

    asyncio.run(run())
