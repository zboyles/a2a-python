import json

from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import httpx

from httpx_sse import connect_sse

from a2a.client.errors import A2AClientHTTPError, A2AClientJSONError
from a2a.types import (
    A2ARequest,
    AgentCard,
    CancelTaskRequest,
    CancelTaskResponse,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    TaskIdParams,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskSendParams,
)


class A2ACardResolver:
    """Agent Card resolver."""

    def __init__(
        self, base_url: str, agent_card_path: str = '/.well-known/agent.json'
    ):
        self.base_url = base_url.rstrip('/')
        self.agent_card_path = agent_card_path.lstrip('/')

    async def get_agent_card(self) -> AgentCard:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.base_url + '/' + self.agent_card_path
                )
                response.raise_for_status()
                return AgentCard.model_validate(response.json())
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e


class A2AClient:
    """A2A Client."""

    def __init__(
        self, agent_card: AgentCard | None = None, url: str | None = None
    ):
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError('Must provide either agent_card or url')

    @classmethod
    async def get_client_from_agent_card_url(
        cls, base_url: str, agent_card_path: str = '/.well-known/agent.json'
    ) -> 'A2AClient':
        agent_card: AgentCard = await A2ACardResolver(
            base_url=base_url, agent_card_path=agent_card_path
        ).get_agent_card()
        return A2AClient(agent_card=agent_card)

    async def send_task(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> SendTaskResponse:
        request = SendTaskRequest(
            id=request_id, params=TaskSendParams.model_validate(payload)
        )
        return SendTaskResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def send_task_streaming(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> AsyncGenerator[SendTaskStreamingResponse, None]:
        request = SendTaskStreamingRequest(
            id=request_id, params=TaskSendParams.model_validate(payload)
        )
        with (
            httpx.Client(timeout=None) as client,
            connect_sse(
                client, 'POST', self.url, json=request.model_dump(mode='json')
            ) as event_source,
        ):
            try:
                for sse in event_source.iter_sse():
                    yield SendTaskStreamingResponse(**json.loads(sse.data))
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e
            except httpx.RequestError as e:
                raise A2AClientHTTPError(400, str(e)) from e

    async def _send_request(self, request: A2ARequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                # Image generation could take time, adding timeout
                response = await client.post(
                    self.url,
                    json=request.root.model_dump(mode='json'),
                    timeout=30,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e

    async def get_task(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> GetTaskResponse:
        request = GetTaskRequest(
            id=request_id, params=TaskQueryParams.model_validate(payload)
        )
        return GetTaskResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def cancel_task(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> CancelTaskResponse:
        request = CancelTaskRequest(
            id=request_id, params=TaskIdParams.model_validate(payload)
        )
        return CancelTaskResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def set_task_callback(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> SetTaskPushNotificationResponse:
        request = SetTaskPushNotificationRequest(
            id=request_id,
            params=TaskPushNotificationConfig.model_validate(payload),
        )
        return SetTaskPushNotificationResponse(
            **await self._send_request(A2ARequest(root=request))
        )

    async def get_task_callback(
        self, payload: dict[str, Any], request_id: str | int = uuid4().hex
    ) -> GetTaskPushNotificationResponse:
        request = GetTaskPushNotificationRequest(
            id=request_id, params=TaskIdParams.model_validate(payload)
        )
        return GetTaskPushNotificationResponse(
            **await self._send_request(A2ARequest(root=request))
        )
