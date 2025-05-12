import uuid
from a2a.types import (
    Message,
    Part,
    Role,
    SendMessageRequest,
    SendStreamingMessageRequest,
    Task,
    TextPart,
)

def new_agent_text_message(
    text: str, context_id: str | None = None, task_id: str | None = None
) -> Message:
    return Message(
        role=Role.agent,
        parts=[Part(root=TextPart(text=text))],
        messageId=str(uuid.uuid4()),
        taskId=task_id,
        contextId=context_id,
    )
