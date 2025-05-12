import uuid
from a2a.utils.errors import ServerError
from a2a.types import (
    Task,
    Message,
    MessageSendParams,
    TextPart
)

class RequestContext:

    def __init__(
        self,
        request: MessageSendParams | None = None,
        task_id: str | None = None,
        context_id: str | None = None,
        task: Task | None = None,
        related_tasks: list[Task] = []
    ):
        self._params = request
        self._task_id = task_id
        self._context_id = context_id
        self._current_task = task
        self._related_tasks: related_tasks
        # If the task id and context id were provided, make sure they
        # match the request. Otherwise, create them
        if self._params:
            if task_id:
                self._params.message.taskId = task_id
                if task and task.id != task_id:
                    raise ServerError(
                        InvalidParamsError(message='bad task id')
                    )
            else:
                self._check_or_generate_task_id()
            if context_id:
                self._params.message.contextId = context_id
                if task and task.contextId != context_id:
                    raise ServerError(
                        InvalidParamsError(message='bad context id')
                    )
            else:
                self._check_or_generate_context_id()

    def get_user_input(self, delimiter='\n') -> str:
        parts = []
        for part in self._params.message.parts:
            if isinstance(part.root, TextPart):
                parts.append(part.root.text)
        return delimiter.join(parts)

    def attach_related_task(self, task: Task):
        self._related_tasks.append(task)

    @property
    def message(self) -> Message | None:
        return self._params.message if self._params else None

    @property
    def related_tasks(self) -> list[Task]:
        return self._related_tasks

    @property
    def current_task(self) -> Task:
        return self._current_task

    @current_task.setter
    def current_task(self, task: Task):
        self._current_task = task

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def context_id(self) -> str:
        return self._context_id

    def _check_or_generate_task_id(self):
      if not self._task_id and not self._params.message.taskId:
          self._params.message.taskId = str(uuid.uuid4())
      if self._params.message.taskId:
          self._task_id = self._params.message.taskId

    def _check_or_generate_context_id(self):
      if not self._context_id and not self._params.message.contextId:
          self._params.message.taskId = str(uuid.uuid4())
      if self._params.message.contextId:
          self._context_id = self._params.message.contextId
