from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from a2a.server.events.event_queue import Event
from a2a.types import (
    Message,
    MessageSendParams,
    Task,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError


class RequestHandler(ABC):
    """A2A request handler interface."""

    @abstractmethod
    async def on_get_task(self, request: TaskQueryParams) -> Task | None:
        pass

    @abstractmethod
    async def on_cancel_task(self, request: TaskIdParams) -> Task | None:
        pass

    @abstractmethod
    async def on_message_send(
        self, request: MessageSendParams
    ) -> Task | Message:
        pass

    @abstractmethod
    async def on_message_send_stream(
        self, request: MessageSendParams
    ) -> AsyncGenerator[Event, None]:
        raise ServerError(error=UnsupportedOperationError())
        yield

    @abstractmethod
    async def on_set_task_push_notification_config(
        self, request: TaskPushNotificationConfig
    ) -> TaskPushNotificationConfig:
        pass

    @abstractmethod
    async def on_get_task_push_notification_config(
        self, request: TaskIdParams
    ) -> TaskPushNotificationConfig:
        pass

    @abstractmethod
    async def on_resubscribe_to_task(
        self, request: TaskIdParams
    ) -> AsyncGenerator[Event, None]:
        raise ServerError(error=UnsupportedOperationError())
        yield
