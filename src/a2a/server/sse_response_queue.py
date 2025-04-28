import asyncio

from a2a.types import SendTaskStreamingResponse


class SSEResponseQueue:
    """Queue for SSE responses."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[SendTaskStreamingResponse] = asyncio.Queue()

    def enqueue_event(self, event: SendTaskStreamingResponse):
        self.queue.put_nowait(event)

    async def dequeue_event(self) -> SendTaskStreamingResponse:
        return await self.queue.get()
