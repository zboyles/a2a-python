import json
import logging
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

from .request_handler import RequestHandler

from a2a.server.request_handlers.response_helpers import (
    build_error_response,
    prepare_response_object,
)
from a2a.utils.errors import MethodNotImplementedError, ServerError
from a2a.types import (
    A2AError,
    A2ARequest,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    CancelTaskSuccessResponse,
    GetTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigResponse,
    GetTaskPushNotificationConfigSuccessResponse,
    GetTaskRequest,
    GetTaskResponse,
    GetTaskSuccessResponse,
    InternalError,
    InvalidRequestError,
    JSONParseError,
    JSONRPCError,
    JSONRPCErrorResponse,
    JSONRPCResponse,
    Message,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    SendStreamingMessageRequest,
    SendStreamingMessageResponse,
    SendStreamingMessageSuccessResponse,
    SetTaskPushNotificationConfigRequest,
    SetTaskPushNotificationConfigResponse,
    SetTaskPushNotificationConfigSuccessResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent,
    TaskResubscriptionRequest,
    UnsupportedOperationError,
)


logger = logging.getLogger(__name__)


class JSONRPCHandler:
    """A handler that maps the JSONRPC Objects to the request handler and back."""

    def __init__(
        self, agent_card: AgentCard,
        request_handler: RequestHandler,
    ):
        """Initializes the HttpProducer.

        Args:
            agent_card: The AgentCard describing the agent's capabilities.
            request_handler: The handler instance responsible for processing A2A requests.
        """
        self.agent_card = agent_card
        self.request_handler = request_handler

    # message/send
    async def on_message_send(
        self, request: SendMessageRequest
    ) -> SendMessageResponse:
        # TODO: Wrap in error handler to return error states
        try:
            task_or_message = await self.request_handler.on_message_send(
                request.params
            )
            return prepare_response_object(
                request.id,
                task_or_message,
                (Task, Message),
                SendMessageSuccessResponse,
                SendMessageResponse,
            )
        except ServerError as e:
            return SendMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # message/stream
    async def on_message_send_stream(
        self, request: SendStreamingMessageRequest
    ) -> AsyncIterable[SendStreamingMessageResponse]:
        try:
          async for event in self.request_handler.on_message_send_stream(request.params):
              yield prepare_response_object(
                request.id,
                event,
                (Task, Message, TaskArtifactUpdateEvent, TaskStatusUpdateEvent),
                SendStreamingMessageSuccessResponse,
                SendStreamingMessageResponse,
            )
        except ServerError as e:
            yield SendStreamingMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # tasks/cancel
    async def on_cancel_task(
        self, request: CancelTaskRequest
    ) -> CancelTaskResponse | None:
        try:
            task = await self.request_handler.on_cancel_task(request.params)
            if task:
                return prepare_response_object(
                    request.id,
                    task,
                    (Task,),
                    CancelTaskSuccessResponse,
                    CancelTaskResponse,
                )
        except ServerError as e:
            return CancelTaskResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # tasks/resubscribe
    async def on_resubscribe_to_task(
        self, request: TaskResubscriptionRequest
    ) ->  AsyncIterable[SendStreamingMessageResponse]:
        try:
            async for event in self.request_handler.on_resubscribe_to_task(request.params):
                yield prepare_response_object(
                    request.id,
                    event,
                    (Task, Message, TaskArtifactUpdateEvent, TaskStatusUpdateEvent),
                    SendStreamingMessageSuccessResponse,
                    SendStreamingMessageResponse,
                )
        except ServerError as e:
            yield SendStreamingMessageResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # tasks/pushNotification/get
    async def get_push_notification(
        self, request: GetTaskPushNotificationConfigRequest
    ) -> GetTaskPushNotificationConfigResponse:
        try:
            config = await self.request_handler.on_get_push_notification(
                request.params)
            return prepare_response_object(
                request.id,
                config,
                (TaskPushNotificationConfig,),
                GetTaskPushNotificationSuccessResponse,
                GetTaskPushNotificationResponse
            )
        except ServerError as e:
            return GetTaskPushNotificationResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # tasks/pushNotification/set
    async def set_push_notification(
        self, request: SetTaskPushNotificationConfigRequest
    ) -> SetTaskPushNotificationConfigResponse:
        try:
            config = await self.request_handler.on_set_push_notification(
                request.params)
            return prepare_response_object(
                request.id,
                config,
                (TaskPushNotificationConfig,),
                SetTaskPushNotificationConfigSuccessResponse,
                SetTaskPushNotificationConfigResponse
            )
        except ServerError as e:
            return SetTaskPushNotificationConfigResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )

    # tasks/get
    async def on_get_task(self, request: GetTaskRequest) -> GetTaskResponse:
        try:
            task = await self.request_handler.on_get_task(request.params)
            result = prepare_response_object(
                request.id,
                task,
                (Task,),
                GetTaskSuccessResponse,
                GetTaskResponse,
            )
            return result
        except ServerError as e:
            return GetTaskResponse(
                root=JSONRPCErrorResponse(
                    id=request.id, error=e.error
                )
            )
