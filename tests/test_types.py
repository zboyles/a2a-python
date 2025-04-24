from typing import Any

import pytest

from pydantic import ValidationError

from a2a.types import (
    A2ARequest,
    AgentAuthentication,
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Artifact,
    CancelTaskRequest,
    CancelTaskResponse,
    ContentTypeNotSupportedError,
    DataPart,
    FileBase,
    FilePart,
    FileWithBytes,
    FileWithUri,
    GetTaskPushNotificationRequest,
    GetTaskPushNotificationResponse,
    GetTaskRequest,
    GetTaskResponse,
    InternalError,
    InvalidParamsError,
    InvalidRequestError,
    JSONParseError,
    JSONRPCError,
    JSONRPCErrorResponse,
    JSONRPCMessage,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCSuccessResponse,
    Message,
    MethodNotFoundError,
    Part,
    PartBase,
    PushNotificationAuthenticationInfo,
    PushNotificationConfig,
    PushNotificationNotSupportedError,
    Role,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    SetTaskPushNotificationRequest,
    SetTaskPushNotificationResponse,
    Task,
    TaskArtifactUpdateEvent,
    TaskIdParams,
    TaskNotCancelableError,
    TaskNotFoundError,
    TaskPushNotificationConfig,
    TaskQueryParams,
    TaskResubscriptionRequest,
    TaskSendParams,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    UnsupportedOperationError,
)


# --- Helper Data ---

MINIMAL_AGENT_AUTH: dict[str, Any] = {'schemes': ['Bearer']}
FULL_AGENT_AUTH: dict[str, Any] = {
    'schemes': ['Bearer', 'Basic'],
    'credentials': 'user:pass',
}

MINIMAL_AGENT_SKILL: dict[str, Any] = {
    'id': 'skill-123',
    'name': 'Recipe Finder',
    'description': 'Finds recipes',
    'tags': ['cooking'],
}
FULL_AGENT_SKILL: dict[str, Any] = {
    'id': 'skill-123',
    'name': 'Recipe Finder',
    'description': 'Finds recipes',
    'tags': ['cooking', 'food'],
    'examples': ['Find me a pasta recipe'],
    'inputModes': ['text/plain'],
    'outputModes': ['application/json'],
}

MINIMAL_AGENT_CARD: dict[str, Any] = {
    'authentication': MINIMAL_AGENT_AUTH,
    'capabilities': {},  # AgentCapabilities is required but can be empty
    'defaultInputModes': ['text/plain'],
    'defaultOutputModes': ['application/json'],
    'description': 'Test Agent',
    'name': 'TestAgent',
    'skills': [MINIMAL_AGENT_SKILL],
    'url': 'http://example.com/agent',
    'version': '1.0',
}

TEXT_PART_DATA: dict[str, Any] = {'type': 'text', 'text': 'Hello'}
FILE_URI_PART_DATA: dict[str, Any] = {
    'type': 'file',
    'file': {'uri': 'file:///path/to/file.txt', 'mimeType': 'text/plain'},
}
FILE_BYTES_PART_DATA: dict[str, Any] = {
    'type': 'file',
    'file': {'bytes': 'aGVsbG8=', 'name': 'hello.txt'},  # base64 for "hello"
}
DATA_PART_DATA: dict[str, Any] = {'type': 'data', 'data': {'key': 'value'}}

MINIMAL_MESSAGE_USER: dict[str, Any] = {
    'role': 'user',
    'parts': [TEXT_PART_DATA],
}

AGENT_MESSAGE_WITH_FILE: dict[str, Any] = {
    'role': 'agent',
    'parts': [TEXT_PART_DATA, FILE_URI_PART_DATA],
    'metadata': {'timestamp': 'now'},
}

MINIMAL_TASK_STATUS: dict[str, Any] = {'state': 'submitted'}
FULL_TASK_STATUS: dict[str, Any] = {
    'state': 'working',
    'message': MINIMAL_MESSAGE_USER,
    'timestamp': '2023-10-27T10:00:00Z',
}

MINIMAL_TASK: dict[str, Any] = {
    'id': 'task-abc',
    'sessionId': 'session-xyz',
    'status': MINIMAL_TASK_STATUS,
}
FULL_TASK: dict[str, Any] = {
    'id': 'task-abc',
    'sessionId': 'session-xyz',
    'status': FULL_TASK_STATUS,
    'history': [MINIMAL_MESSAGE_USER, AGENT_MESSAGE_WITH_FILE],
    'artifacts': [
        {'index': 0, 'parts': [DATA_PART_DATA], 'name': 'result_data'}
    ],
    'metadata': {'priority': 'high'},
}

MINIMAL_TASK_ID_PARAMS: dict[str, Any] = {'id': 'task-123'}
FULL_TASK_ID_PARAMS: dict[str, Any] = {
    'id': 'task-456',
    'metadata': {'source': 'test'},
}

JSONRPC_ERROR_DATA: dict[str, Any] = {
    'code': -32600,
    'message': 'Invalid Request',
}
JSONRPC_SUCCESS_RESULT: dict[str, Any] = {'status': 'ok', 'data': [1, 2, 3]}

# --- Test Functions ---


def test_agent_authentication_valid():
    auth = AgentAuthentication(**MINIMAL_AGENT_AUTH)
    assert auth.schemes == ['Bearer']
    assert auth.credentials is None

    auth_full = AgentAuthentication(**FULL_AGENT_AUTH)
    assert auth_full.schemes == ['Bearer', 'Basic']
    assert auth_full.credentials == 'user:pass'


def test_agent_authentication_invalid():
    with pytest.raises(ValidationError):
        AgentAuthentication(
            credentials='only_creds'
        )  # Missing schemes  # type: ignore
    with pytest.raises(ValidationError):
        AgentAuthentication(
            schemes=['Bearer'],
            extra_field='invalid',  # type: ignore
        )  # Extra field


def test_agent_capabilities():
    caps = AgentCapabilities(
        streaming=None, stateTransitionHistory=None, pushNotifications=None
    )  # All optional
    assert caps.pushNotifications is None
    assert caps.stateTransitionHistory is None
    assert caps.streaming is None

    caps_full = AgentCapabilities(
        pushNotifications=True, stateTransitionHistory=False, streaming=True
    )
    assert caps_full.pushNotifications is True
    assert caps_full.stateTransitionHistory is False
    assert caps_full.streaming is True


def test_agent_provider():
    provider = AgentProvider(organization='Test Org', url='http://test.org')
    assert provider.organization == 'Test Org'
    assert provider.url == 'http://test.org'

    with pytest.raises(ValidationError):
        AgentProvider(organization='Test Org')  # Missing url  # type: ignore


def test_agent_skill_valid():
    skill = AgentSkill(**MINIMAL_AGENT_SKILL)
    assert skill.id == 'skill-123'
    assert skill.name == 'Recipe Finder'
    assert skill.description == 'Finds recipes'
    assert skill.tags == ['cooking']
    assert skill.examples is None

    skill_full = AgentSkill(**FULL_AGENT_SKILL)
    assert skill_full.examples == ['Find me a pasta recipe']
    assert skill_full.inputModes == ['text/plain']


def test_agent_skill_invalid():
    with pytest.raises(ValidationError):
        AgentSkill(
            id='abc', name='n', description='d'
        )  # Missing tags  # type: ignore
    with pytest.raises(ValidationError):
        AgentSkill(
            **MINIMAL_AGENT_SKILL,
            invalid_extra='foo',  # type: ignore
        )  # Extra field


def test_agent_card_valid():
    card = AgentCard(**MINIMAL_AGENT_CARD)
    assert card.name == 'TestAgent'
    assert card.version == '1.0'
    assert card.authentication.schemes == ['Bearer']
    assert len(card.skills) == 1
    assert card.skills[0].id == 'skill-123'
    assert card.provider is None  # Optional


def test_agent_card_invalid():
    bad_card_data = MINIMAL_AGENT_CARD.copy()
    del bad_card_data['name']
    with pytest.raises(ValidationError):
        AgentCard(**bad_card_data)  # Missing name


# --- Test Parts ---


def test_text_part():
    part = TextPart(**TEXT_PART_DATA)
    assert part.type == 'text'
    assert part.text == 'Hello'
    assert part.metadata is None

    with pytest.raises(ValidationError):
        TextPart(type='text')  # Missing text # type: ignore
    with pytest.raises(ValidationError):
        TextPart(
            type='file',
            text='hello',  # type: ignore
        )  # Wrong type literal


def test_file_part_variants():
    # URI variant
    file_uri = FileWithUri(
        uri='file:///path/to/file.txt', mimeType='text/plain'
    )
    part_uri = FilePart(type='file', file=file_uri)
    assert isinstance(part_uri.file, FileWithUri)
    assert part_uri.file.uri == 'file:///path/to/file.txt'
    assert part_uri.file.mimeType == 'text/plain'
    assert not hasattr(part_uri.file, 'bytes')

    # Bytes variant
    file_bytes = FileWithBytes(bytes='aGVsbG8=', name='hello.txt')
    part_bytes = FilePart(type='file', file=file_bytes)
    assert isinstance(part_bytes.file, FileWithBytes)
    assert part_bytes.file.bytes == 'aGVsbG8='
    assert part_bytes.file.name == 'hello.txt'
    assert not hasattr(part_bytes.file, 'uri')

    # Test deserialization directly
    part_uri_deserialized = FilePart.model_validate(FILE_URI_PART_DATA)
    assert isinstance(part_uri_deserialized.file, FileWithUri)
    assert part_uri_deserialized.file.uri == 'file:///path/to/file.txt'

    part_bytes_deserialized = FilePart.model_validate(FILE_BYTES_PART_DATA)
    assert isinstance(part_bytes_deserialized.file, FileWithBytes)
    assert part_bytes_deserialized.file.bytes == 'aGVsbG8='

    # Invalid - wrong type literal
    with pytest.raises(ValidationError):
        FilePart(type='text', file=file_uri)  # type: ignore
    # Invalid - extra field
    with pytest.raises(ValidationError):
        FilePart(**FILE_URI_PART_DATA, extra='bad')  # type: ignore


def test_data_part():
    part = DataPart(**DATA_PART_DATA)
    assert part.type == 'data'
    assert part.data == {'key': 'value'}

    with pytest.raises(ValidationError):
        DataPart(type='data')  # Missing data  # type: ignore


def test_part_root_model():
    # Test deserialization of the Union RootModel
    part_text = Part.model_validate(TEXT_PART_DATA)
    assert isinstance(part_text.root, TextPart)
    assert part_text.root.text == 'Hello'

    part_file = Part.model_validate(FILE_URI_PART_DATA)
    assert isinstance(part_file.root, FilePart)
    assert isinstance(part_file.root.file, FileWithUri)

    part_data = Part.model_validate(DATA_PART_DATA)
    assert isinstance(part_data.root, DataPart)
    assert part_data.root.data == {'key': 'value'}

    # Test serialization
    assert part_text.model_dump(exclude_none=True) == TEXT_PART_DATA
    assert part_file.model_dump(exclude_none=True) == FILE_URI_PART_DATA
    assert part_data.model_dump(exclude_none=True) == DATA_PART_DATA


# --- Test Message and Task ---


def test_message():
    msg = Message(**MINIMAL_MESSAGE_USER)
    assert msg.role == Role.user
    assert len(msg.parts) == 1
    assert isinstance(
        msg.parts[0].root, TextPart
    )  # Access root for RootModel Part
    assert msg.metadata is None

    msg_agent = Message(**AGENT_MESSAGE_WITH_FILE)
    assert msg_agent.role == Role.agent
    assert len(msg_agent.parts) == 2
    assert isinstance(msg_agent.parts[1].root, FilePart)
    assert msg_agent.metadata == {'timestamp': 'now'}

    with pytest.raises(ValidationError):
        Message(
            role='invalid_role',
            parts=[TEXT_PART_DATA],  # type: ignore
        )  # Invalid enum
    with pytest.raises(ValidationError):
        Message(role='user')  # Missing parts  # type: ignore


def test_task_status():
    status = TaskStatus(**MINIMAL_TASK_STATUS)
    assert status.state == TaskState.submitted
    assert status.message is None
    assert status.timestamp is None

    status_full = TaskStatus(**FULL_TASK_STATUS)
    assert status_full.state == TaskState.working
    assert isinstance(status_full.message, Message)
    assert status_full.timestamp == '2023-10-27T10:00:00Z'

    with pytest.raises(ValidationError):
        TaskStatus(state='invalid_state')  # Invalid enum  # type: ignore


def test_task():
    task = Task(**MINIMAL_TASK)
    assert task.id == 'task-abc'
    assert task.sessionId == 'session-xyz'
    assert task.status.state == TaskState.submitted
    assert task.history is None
    assert task.artifacts is None
    assert task.metadata is None

    task_full = Task(**FULL_TASK)
    assert task_full.id == 'task-abc'
    assert task_full.status.state == TaskState.working
    assert task_full.history is not None and len(task_full.history) == 2
    assert isinstance(task_full.history[0], Message)
    assert task_full.artifacts is not None and len(task_full.artifacts) == 1
    assert isinstance(task_full.artifacts[0], Artifact)
    assert task_full.artifacts[0].name == 'result_data'
    assert task_full.metadata == {'priority': 'high'}

    with pytest.raises(ValidationError):
        Task(id='abc', sessionId='xyz')  # Missing status # type: ignore


# --- Test JSON-RPC Structures ---


def test_jsonrpc_error():
    err = JSONRPCError(code=-32600, message='Invalid Request')
    assert err.code == -32600
    assert err.message == 'Invalid Request'
    assert err.data is None

    err_data = JSONRPCError(
        code=-32001, message='Task not found', data={'taskId': '123'}
    )
    assert err_data.code == -32001
    assert err_data.data == {'taskId': '123'}


def test_jsonrpc_request():
    req = JSONRPCRequest(jsonrpc='2.0', method='test_method', id=1)
    assert req.jsonrpc == '2.0'
    assert req.method == 'test_method'
    assert req.id == 1
    assert req.params is None

    req_params = JSONRPCRequest(
        jsonrpc='2.0', method='add', params={'a': 1, 'b': 2}, id='req-1'
    )
    assert req_params.params == {'a': 1, 'b': 2}
    assert req_params.id == 'req-1'

    with pytest.raises(ValidationError):
        JSONRPCRequest(
            jsonrpc='1.0',
            method='m',
            id=1,  # type: ignore
        )  # Wrong version
    with pytest.raises(ValidationError):
        JSONRPCRequest(jsonrpc='2.0', id=1)  # Missing method  # type: ignore


def test_jsonrpc_success_response():
    resp = JSONRPCSuccessResponse(
        jsonrpc='2.0', result=JSONRPC_SUCCESS_RESULT, id=1
    )
    assert resp.jsonrpc == '2.0'
    assert resp.result == JSONRPC_SUCCESS_RESULT
    assert resp.id == 1

    with pytest.raises(ValidationError):
        JSONRPCSuccessResponse(
            jsonrpc='2.0', id=1
        )  # Missing result # type: ignore


def test_jsonrpc_error_response():
    err_obj = JSONRPCError(**JSONRPC_ERROR_DATA)
    resp = JSONRPCErrorResponse(jsonrpc='2.0', error=err_obj, id='err-1')
    assert resp.jsonrpc == '2.0'
    assert resp.id == 'err-1'
    assert resp.error.code == -32600
    assert resp.error.message == 'Invalid Request'

    with pytest.raises(ValidationError):
        JSONRPCErrorResponse(
            jsonrpc='2.0', id='err-1'
        )  # Missing error # type: ignore


def test_jsonrpc_response_root_model() -> None:
    # Success case
    success_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': {'status': 'ok'},
        'id': 1,
    }
    resp_success = JSONRPCResponse.model_validate(success_data)
    assert isinstance(resp_success.root, JSONRPCSuccessResponse)
    assert resp_success.root.result == {'status': 'ok'}
    assert resp_success.model_dump(exclude_none=True) == success_data

    # Error case
    error_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'error': JSONRPC_ERROR_DATA,
        'id': 'err-1',
    }
    resp_error = JSONRPCResponse.model_validate(error_data)
    assert isinstance(resp_error.root, JSONRPCErrorResponse)
    assert resp_error.root.error.code == -32600
    # Note: .model_dump() might serialize the nested error model
    assert resp_error.model_dump(exclude_none=True) == error_data

    # Invalid case (neither success nor error structure)
    with pytest.raises(ValidationError):
        JSONRPCResponse.model_validate({'jsonrpc': '2.0', 'id': 1})


# --- Test Request/Response Wrappers ---


def test_send_task_request() -> None:
    params = TaskSendParams(
        id='task-1', message=Message(**MINIMAL_MESSAGE_USER)
    )
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/send',
        'params': params.model_dump(),
        'id': 5,
    }
    req = SendTaskRequest.model_validate(req_data)
    assert req.method == 'tasks/send'
    assert isinstance(req.params, TaskSendParams)
    assert req.params.id == 'task-1'
    assert req.params.message.role == Role.user

    with pytest.raises(ValidationError):  # Wrong method literal
        SendTaskRequest.model_validate({**req_data, 'method': 'wrong/method'})


def test_send_subscribe_request() -> None:
    params = TaskSendParams(
        id='task-1', message=Message(**MINIMAL_MESSAGE_USER)
    )
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/sendSubscribe',
        'params': params.model_dump(),
        'id': 5,
    }
    req = SendTaskStreamingRequest.model_validate(req_data)
    assert req.method == 'tasks/sendSubscribe'
    assert isinstance(req.params, TaskSendParams)
    assert req.params.id == 'task-1'
    assert req.params.message.role == Role.user

    with pytest.raises(ValidationError):  # Wrong method literal
        SendTaskStreamingRequest.model_validate(
            {**req_data, 'method': 'wrong/method'}
        )


def test_get_task_request() -> None:
    params = TaskQueryParams(id='task-1', historyLength=2)
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/get',
        'params': params.model_dump(),
        'id': 5,
    }
    req = GetTaskRequest.model_validate(req_data)
    assert req.method == 'tasks/get'
    assert isinstance(req.params, TaskQueryParams)
    assert req.params.id == 'task-1'
    assert req.params.historyLength == 2

    with pytest.raises(ValidationError):  # Wrong method literal
        GetTaskRequest.model_validate({**req_data, 'method': 'wrong/method'})


def test_cancel_task_request() -> None:
    params = TaskIdParams(id='task-1')
    req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/cancel',
        'params': params.model_dump(),
        'id': 5,
    }
    req = CancelTaskRequest.model_validate(req_data)
    assert req.method == 'tasks/cancel'
    assert isinstance(req.params, TaskIdParams)
    assert req.params.id == 'task-1'

    with pytest.raises(ValidationError):  # Wrong method literal
        CancelTaskRequest.model_validate({**req_data, 'method': 'wrong/method'})


def test_get_task_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 'resp-1',
    }
    resp = GetTaskResponse.model_validate(resp_data)
    assert resp.id == 'resp-1'
    assert isinstance(resp.result, Task)
    assert resp.result.id == 'task-abc'

    with pytest.raises(ValidationError):  # Result is not a Task
        GetTaskResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )


def test_send_task_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 'resp-1',
    }
    resp = SendTaskResponse.model_validate(resp_data)
    assert resp.id == 'resp-1'
    assert isinstance(resp.result, Task)
    assert resp.result.id == 'task-abc'

    with pytest.raises(ValidationError):  # Result is not a Task
        SendTaskResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )


def test_cancel_task_response() -> None:
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': MINIMAL_TASK,
        'id': 1,
    }
    resp = CancelTaskResponse.model_validate(resp_data)
    assert resp.id == 1
    assert isinstance(resp.result, Task)
    assert resp.result.id == 'task-abc'


def test_send_task_streaming_status_update_response() -> None:
    task_status_update_event_data: dict[str, Any] = {
        'status': MINIMAL_TASK_STATUS,
        'id': '1',
        'final': False,
    }

    event_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': task_status_update_event_data,
    }
    response = SendTaskStreamingResponse.model_validate(event_data)
    assert response.id == 1
    assert isinstance(response.result, TaskStatusUpdateEvent)
    assert response.result.status.state == TaskState.submitted
    assert response.result.id == '1'
    assert not response.result.final

    with pytest.raises(
        ValidationError
    ):  # Result is not a TaskStatusUpdateEvent
        SendTaskStreamingResponse.model_validate(
            {'jsonrpc': '2.0', 'result': {'wrong': 'data'}, 'id': 1}
        )

    event_data = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': {**task_status_update_event_data, 'final': True},
    }
    response = SendTaskStreamingResponse.model_validate(event_data)
    assert response.id == 1
    assert isinstance(response.result, TaskStatusUpdateEvent)
    assert response.result.final


def test_send_task_streaming_artifact_update_response() -> None:
    text_part = TextPart(**TEXT_PART_DATA)
    data_part = DataPart(**DATA_PART_DATA)
    artifact = Artifact(
        index=0,
        name='result_data',
        parts=[Part(root=text_part), Part(root=data_part)],
    )
    task_artifact_update_event_data: dict[str, Any] = {
        'artifact': artifact,
        'id': 'task_id',
        'append': False,
        'lastChunk': True,
    }
    event_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'id': 1,
        'result': task_artifact_update_event_data,
    }
    response = SendTaskStreamingResponse.model_validate(event_data)
    assert response.id == 1
    assert isinstance(response.result, TaskArtifactUpdateEvent)
    assert response.result.artifact.index == 0
    assert response.result.artifact.name == 'result_data'
    assert response.result.id == 'task_id'
    assert not response.result.append
    assert response.result.lastChunk
    assert len(response.result.artifact.parts) == 2
    assert isinstance(response.result.artifact.parts[0].root, TextPart)
    assert isinstance(response.result.artifact.parts[1].root, DataPart)


def test_set_task_push_notification_response() -> None:
    task_push_config = TaskPushNotificationConfig(
        id='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = SetTaskPushNotificationResponse.model_validate(resp_data)
    assert resp.id == 1
    assert isinstance(resp.result, TaskPushNotificationConfig)
    assert resp.result.id == 't2'
    assert resp.result.pushNotificationConfig.url == 'https://example.com'
    assert resp.result.pushNotificationConfig.token == 'token'
    assert resp.result.pushNotificationConfig.authentication is None

    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    task_push_config.pushNotificationConfig.authentication = (
        PushNotificationAuthenticationInfo(**auth_info_dict)
    )
    resp_data = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = SetTaskPushNotificationResponse.model_validate(resp_data)
    assert resp.result.pushNotificationConfig.authentication is not None
    assert resp.result.pushNotificationConfig.authentication.schemes == [
        'Bearer',
        'Basic',
    ]
    assert (
        resp.result.pushNotificationConfig.authentication.credentials
        == 'user:pass'
    )


def test_get_task_push_notification_response() -> None:
    task_push_config = TaskPushNotificationConfig(
        id='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    resp_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = GetTaskPushNotificationResponse.model_validate(resp_data)
    assert resp.id == 1
    assert isinstance(resp.result, TaskPushNotificationConfig)
    assert resp.result.id == 't2'
    assert resp.result.pushNotificationConfig.url == 'https://example.com'
    assert resp.result.pushNotificationConfig.token == 'token'
    assert resp.result.pushNotificationConfig.authentication is None

    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    task_push_config.pushNotificationConfig.authentication = (
        PushNotificationAuthenticationInfo(**auth_info_dict)
    )
    resp_data = {
        'jsonrpc': '2.0',
        'result': task_push_config.model_dump(),
        'id': 1,
    }
    resp = GetTaskPushNotificationResponse.model_validate(resp_data)
    assert resp.result.pushNotificationConfig.authentication is not None
    assert resp.result.pushNotificationConfig.authentication.schemes == [
        'Bearer',
        'Basic',
    ]
    assert (
        resp.result.pushNotificationConfig.authentication.credentials
        == 'user:pass'
    )


# --- Test A2ARequest Root Model ---


def test_a2a_request_root_model() -> None:
    # SendTaskRequest case
    send_params = TaskSendParams(
        id='t1', message=Message(**MINIMAL_MESSAGE_USER)
    )
    send_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/send',
        'params': send_params.model_dump(),
        'id': 1,
    }
    a2a_req_send = A2ARequest.model_validate(send_req_data)
    assert isinstance(a2a_req_send.root, SendTaskRequest)
    assert a2a_req_send.root.method == 'tasks/send'

    # SendTaskStreamingRequest case
    send_subs_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/sendSubscribe',
        'params': send_params.model_dump(),
        'id': 1,
    }
    a2a_req_send_subs = A2ARequest.model_validate(send_subs_req_data)
    assert isinstance(a2a_req_send_subs.root, SendTaskStreamingRequest)
    assert a2a_req_send_subs.root.method == 'tasks/sendSubscribe'

    # GetTaskRequest case
    get_params = TaskQueryParams(id='t2')
    get_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/get',
        'params': get_params.model_dump(),
        'id': 2,
    }
    a2a_req_get = A2ARequest.model_validate(get_req_data)
    assert isinstance(a2a_req_get.root, GetTaskRequest)
    assert a2a_req_get.root.method == 'tasks/get'

    # CancelTaskRequest case
    id_params = TaskIdParams(id='t2')
    cancel_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/cancel',
        'params': id_params.model_dump(),
        'id': 2,
    }
    a2a_req_cancel = A2ARequest.model_validate(cancel_req_data)
    assert isinstance(a2a_req_cancel.root, CancelTaskRequest)
    assert a2a_req_cancel.root.method == 'tasks/cancel'

    # SetTaskPushNotificationRequest
    task_push_config = TaskPushNotificationConfig(
        id='t2',
        pushNotificationConfig=PushNotificationConfig(
            url='https://example.com', token='token'
        ),
    )
    set_push_notif_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/pushNotification/set',
        'params': task_push_config.model_dump(),
        'id': 2,
    }
    a2a_req_set_push_req = A2ARequest.model_validate(set_push_notif_req_data)
    assert isinstance(a2a_req_set_push_req.root, SetTaskPushNotificationRequest)
    assert isinstance(
        a2a_req_set_push_req.root.params, TaskPushNotificationConfig
    )
    assert a2a_req_set_push_req.root.method == 'tasks/pushNotification/set'

    # GetTaskPushNotificationRequest
    id_params = TaskIdParams(id='t2')
    get_push_notif_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/pushNotification/get',
        'params': id_params.model_dump(),
        'id': 2,
    }
    a2a_req_get_push_req = A2ARequest.model_validate(get_push_notif_req_data)
    assert isinstance(a2a_req_get_push_req.root, GetTaskPushNotificationRequest)
    assert isinstance(a2a_req_get_push_req.root.params, TaskIdParams)
    assert a2a_req_get_push_req.root.method == 'tasks/pushNotification/get'

    # TaskResubscriptionRequest
    task_resubscribe_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'tasks/resubscribe',
        'params': id_params.model_dump(),
        'id': 2,
    }
    a2a_req_task_resubscribe_req = A2ARequest.model_validate(
        task_resubscribe_req_data
    )
    assert isinstance(
        a2a_req_task_resubscribe_req.root, TaskResubscriptionRequest
    )
    assert isinstance(a2a_req_task_resubscribe_req.root.params, TaskIdParams)
    assert a2a_req_task_resubscribe_req.root.method == 'tasks/resubscribe'

    # Invalid method case
    invalid_req_data: dict[str, Any] = {
        'jsonrpc': '2.0',
        'method': 'invalid/method',
        'params': {},
        'id': 3,
    }
    with pytest.raises(ValidationError):
        A2ARequest.model_validate(invalid_req_data)


def test_content_type_not_supported_error():
    # Test ContentTypeNotSupportedError
    err = ContentTypeNotSupportedError(
        code=-32005, message='Incompatible content types'
    )
    assert err.code == -32005
    assert err.message == 'Incompatible content types'
    assert err.data is None

    with pytest.raises(ValidationError):  # Wrong code
        ContentTypeNotSupportedError(
            code=-32000,  # type: ignore
            message='Incompatible content types',
        )
    with pytest.raises(ValidationError):  # Extra field
        ContentTypeNotSupportedError(
            code=-32005,
            message='Incompatible content types',
            extra='bad',  # type: ignore
        )


def test_task_not_found_error():
    # Test TaskNotFoundError
    err2 = TaskNotFoundError(
        code=-32001, message='Task not found', data={'taskId': 'abc'}
    )
    assert err2.code == -32001
    assert err2.message == 'Task not found'
    assert err2.data == {'taskId': 'abc'}

    with pytest.raises(ValidationError):  # Wrong code
        TaskNotFoundError(code=-32000, message='Task not found')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        TaskNotFoundError(code=-32001, message='Task not found', extra='bad')  # type: ignore


def test_push_notification_not_supported_error():
    # Test PushNotificationNotSupportedError
    err3 = PushNotificationNotSupportedError(data={'taskId': 'abc'})
    assert err3.code == -32003
    assert err3.message == 'Push Notification is not supported'
    assert err3.data == {'taskId': 'abc'}

    with pytest.raises(ValidationError):  # Wrong code
        PushNotificationNotSupportedError(
            code=-32000,  # type: ignore
            message='Push Notification is not available',
        )
    with pytest.raises(ValidationError):  # Extra field
        PushNotificationNotSupportedError(
            code=-32001,
            message='Push Notification is not available',
            extra='bad',  # type: ignore
        )


def test_internal_error():
    # Test InternalError
    err_internal = InternalError()
    assert err_internal.code == -32603
    assert err_internal.message == 'Internal error'
    assert err_internal.data is None

    err_internal_data = InternalError(
        code=-32603, message='Internal error', data={'details': 'stack trace'}
    )
    assert err_internal_data.data == {'details': 'stack trace'}

    with pytest.raises(ValidationError):  # Wrong code
        InternalError(code=-32000, message='Internal error')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        InternalError(code=-32603, message='Internal error', extra='bad')  # type: ignore


def test_invalid_params_error():
    # Test InvalidParamsError
    err_params = InvalidParamsError()
    assert err_params.code == -32602
    assert err_params.message == 'Invalid parameters'
    assert err_params.data is None

    err_params_data = InvalidParamsError(
        code=-32602, message='Invalid parameters', data=['param1', 'param2']
    )
    assert err_params_data.data == ['param1', 'param2']

    with pytest.raises(ValidationError):  # Wrong code
        InvalidParamsError(code=-32000, message='Invalid parameters')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        InvalidParamsError(
            code=-32602,
            message='Invalid parameters',
            extra='bad',  # type: ignore
        )


def test_invalid_request_error():
    # Test InvalidRequestError
    err_request = InvalidRequestError()
    assert err_request.code == -32600
    assert err_request.message == 'Request payload validation error'
    assert err_request.data is None

    err_request_data = InvalidRequestError(data={'field': 'missing'})
    assert err_request_data.data == {'field': 'missing'}

    with pytest.raises(ValidationError):  # Wrong code
        InvalidRequestError(
            code=-32000,  # type: ignore
            message='Request payload validation error',
        )
    with pytest.raises(ValidationError):  # Extra field
        InvalidRequestError(
            code=-32600,
            message='Request payload validation error',
            extra='bad',  # type: ignore
        )  # type: ignore


def test_json_parse_error():
    # Test JSONParseError
    err_parse = JSONParseError(code=-32700, message='Invalid JSON payload')
    assert err_parse.code == -32700
    assert err_parse.message == 'Invalid JSON payload'
    assert err_parse.data is None

    err_parse_data = JSONParseError(data={'foo': 'bar'})  # Explicit None data
    assert err_parse_data.data == {'foo': 'bar'}

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Invalid JSON payload')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        JSONParseError(code=-32700, message='Invalid JSON payload', extra='bad')  # type: ignore


def test_method_not_found_error():
    # Test MethodNotFoundError
    err_parse = MethodNotFoundError()
    assert err_parse.code == -32601
    assert err_parse.message == 'Method not found'
    assert err_parse.data is None

    err_parse_data = JSONParseError(data={'foo': 'bar'})
    assert err_parse_data.data == {'foo': 'bar'}

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Invalid JSON payload')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        JSONParseError(code=-32700, message='Invalid JSON payload', extra='bad')  # type: ignore


def test_task_not_cancelable_error():
    # Test TaskNotCancelableError
    err_parse = TaskNotCancelableError()
    assert err_parse.code == -32002
    assert err_parse.message == 'Task cannot be canceled'
    assert err_parse.data is None

    err_parse_data = JSONParseError(
        data={'foo': 'bar'}, message='not cancelled'
    )
    assert err_parse_data.data == {'foo': 'bar'}
    assert err_parse_data.message == 'not cancelled'

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Task cannot be canceled')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        JSONParseError(
            code=-32700,
            message='Task cannot be canceled',
            extra='bad',  # type: ignore
        )


def test_unsupported_operation_error():
    # Test UnsupportedOperationError
    err_parse = UnsupportedOperationError()
    assert err_parse.code == -32004
    assert err_parse.message == 'This operation is not supported'
    assert err_parse.data is None

    err_parse_data = JSONParseError(
        data={'foo': 'bar'}, message='not supported'
    )
    assert err_parse_data.data == {'foo': 'bar'}
    assert err_parse_data.message == 'not supported'

    with pytest.raises(ValidationError):  # Wrong code
        JSONParseError(code=-32000, message='Unsupported')  # type: ignore
    with pytest.raises(ValidationError):  # Extra field
        JSONParseError(code=-32700, message='Unsupported', extra='bad')  # type: ignore


# --- Test TaskIdParams ---


def test_task_id_params_valid():
    """Tests successful validation of TaskIdParams."""
    # Minimal valid data
    params_min = TaskIdParams(**MINIMAL_TASK_ID_PARAMS)
    assert params_min.id == 'task-123'
    assert params_min.metadata is None

    # Full valid data
    params_full = TaskIdParams(**FULL_TASK_ID_PARAMS)
    assert params_full.id == 'task-456'
    assert params_full.metadata == {'source': 'test'}


def test_task_id_params_invalid():
    """Tests validation errors for TaskIdParams."""
    # Missing required 'id' field
    with pytest.raises(ValidationError) as excinfo_missing:
        TaskIdParams()  # type: ignore
    assert 'id' in str(
        excinfo_missing.value
    )  # Check that 'id' is mentioned in the error

    # Extra field not allowed
    invalid_data = MINIMAL_TASK_ID_PARAMS.copy()
    invalid_data['extra_field'] = 'not_allowed'
    with pytest.raises(ValidationError) as excinfo_extra:
        TaskIdParams(**invalid_data)  # type: ignore
    assert 'extra_field' in str(
        excinfo_extra.value
    )  # Check that the extra field is mentioned

    # Incorrect type for metadata (should be dict)
    invalid_metadata_type = {'id': 'task-789', 'metadata': 'not_a_dict'}
    with pytest.raises(ValidationError) as excinfo_type:
        TaskIdParams(**invalid_metadata_type)  # type: ignore
    assert 'metadata' in str(
        excinfo_type.value
    )  # Check that 'metadata' is mentioned


def test_task_push_notification_config() -> None:
    """Tests successful validation of TaskPushNotificationConfig."""
    auth_info_dict: dict[str, Any] = {
        'schemes': ['Bearer', 'Basic'],
        'credentials': 'user:pass',
    }
    auth_info = PushNotificationAuthenticationInfo(**auth_info_dict)

    push_notification_config = PushNotificationConfig(
        url='https://example.com', token='token', authentication=auth_info
    )
    assert push_notification_config.url == 'https://example.com'
    assert push_notification_config.token == 'token'
    assert push_notification_config.authentication == auth_info

    task_push_notification_config = TaskPushNotificationConfig(
        id='task-123', pushNotificationConfig=push_notification_config
    )
    assert task_push_notification_config.id == 'task-123'
    assert (
        task_push_notification_config.pushNotificationConfig
        == push_notification_config
    )
    assert task_push_notification_config.model_dump(exclude_none=True) == {
        'id': 'task-123',
        'pushNotificationConfig': {
            'url': 'https://example.com',
            'token': 'token',
            'authentication': {
                'schemes': ['Bearer', 'Basic'],
                'credentials': 'user:pass',
            },
        },
    }


def test_jsonrpc_message_valid():
    """Tests successful validation of JSONRPCMessage."""
    # With string ID
    msg_str_id = JSONRPCMessage(jsonrpc='2.0', id='req-1')
    assert msg_str_id.jsonrpc == '2.0'
    assert msg_str_id.id == 'req-1'

    # With integer ID (will be coerced to float by Pydantic for JSON number compatibility)
    msg_int_id = JSONRPCMessage(jsonrpc='2.0', id=1)
    assert msg_int_id.jsonrpc == '2.0'
    assert (
        msg_int_id.id == 1
    )  # Pydantic v2 keeps int if possible, but float is in type hint

    # With None ID
    msg_none_id = JSONRPCMessage(jsonrpc='2.0', id=None)
    assert msg_none_id.jsonrpc == '2.0'
    assert msg_none_id.id is None

    # Without ID (defaults to None)
    msg_no_id = JSONRPCMessage(jsonrpc='2.0')
    assert msg_no_id.jsonrpc == '2.0'
    assert msg_no_id.id is None

    rpc_message = JSONRPCMessage(id=1)
    assert rpc_message.jsonrpc == '2.0'
    assert rpc_message.id == 1


def test_jsonrpc_message_invalid():
    """Tests validation errors for JSONRPCMessage."""
    # Incorrect jsonrpc version
    with pytest.raises(ValidationError):
        JSONRPCMessage(jsonrpc='1.0', id=1)  # type: ignore

    # Extra field not allowed
    with pytest.raises(ValidationError):
        JSONRPCMessage(jsonrpc='2.0', id=1, extra_field='invalid')  # type: ignore

    # Invalid ID type (e.g., list) - Pydantic should catch this based on type hints
    with pytest.raises(ValidationError):
        JSONRPCMessage(jsonrpc='2.0', id=[1, 2])  # type: ignore


def test_file_base_valid():
    """Tests successful validation of FileBase."""
    # No optional fields
    base1 = FileBase()
    assert base1.mimeType is None
    assert base1.name is None

    # With mimeType only
    base2 = FileBase(mimeType='image/png')
    assert base2.mimeType == 'image/png'
    assert base2.name is None

    # With name only
    base3 = FileBase(name='document.pdf')
    assert base3.mimeType is None
    assert base3.name == 'document.pdf'

    # With both fields
    base4 = FileBase(mimeType='application/json', name='data.json')
    assert base4.mimeType == 'application/json'
    assert base4.name == 'data.json'


def test_file_base_invalid():
    """Tests validation errors for FileBase."""
    # Extra field not allowed
    with pytest.raises(ValidationError) as excinfo_extra:
        FileBase(extra_field='not_allowed')  # type: ignore
    assert 'extra_field' in str(excinfo_extra.value)

    # Incorrect type for mimeType
    with pytest.raises(ValidationError) as excinfo_type_mime:
        FileBase(mimeType=123)  # type: ignore
    assert 'mimeType' in str(excinfo_type_mime.value)

    # Incorrect type for name
    with pytest.raises(ValidationError) as excinfo_type_name:
        FileBase(name=['list', 'is', 'wrong'])  # type: ignore
    assert 'name' in str(excinfo_type_name.value)


def test_part_base_valid() -> None:
    """Tests successful validation of PartBase."""
    # No optional fields (metadata is None)
    base1 = PartBase()
    assert base1.metadata is None

    # With metadata
    meta_data: dict[str, Any] = {'source': 'test', 'timestamp': 12345}
    base2 = PartBase(metadata=meta_data)
    assert base2.metadata == meta_data


def test_part_base_invalid():
    """Tests validation errors for PartBase."""
    # Extra field not allowed
    with pytest.raises(ValidationError) as excinfo_extra:
        PartBase(extra_field='forbidden')  # type: ignore
    assert 'extra_field' in str(excinfo_extra.value)

    # Incorrect type for metadata (should be dict)
    with pytest.raises(ValidationError) as excinfo_type:
        PartBase(metadata='not_a_dict')  # type: ignore
    assert 'metadata' in str(excinfo_type.value)
