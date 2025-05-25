import json
import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete, update

from a2a.server.models import Base, TaskModel  # TaskModel is our SQLAlchemy model
from a2a.server.tasks.task_store import TaskStore
from a2a.types import Task, TaskStatus  # Task is the Pydantic model

logger = logging.getLogger(__name__)


class DatabaseTaskStore(TaskStore):
    """
    SQLAlchemy-based implementation of TaskStore.
    Stores task objects in a database supported by SQLAlchemy.
    """

    def __init__(
        self,
        db_url: str,
        create_table: bool = True,
    ) -> None:
        """
        Initializes the DatabaseTaskStore.

        Args:
            db_url: Database connection string.
            create_table: If true, create tasks table on initialization.
        """
        logger.debug(f"Initializing DatabaseTaskStore with DB URL: {db_url}")
        self.engine = create_async_engine(db_url, echo=False)  # Set echo=True for SQL logging
        self.async_session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.create_table = create_table
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize the database and create the table if needed.
        """
        if self._initialized:
            return

        logger.debug("Initializing database schema...")
        if self.create_table:
            async with self.engine.begin() as conn:
                # This will create the 'tasks' table based on TaskModel's definition
                await conn.run_sync(Base.metadata.create_all)
        self._initialized = True
        logger.debug("Database schema initialized.")

    async def close(self) -> None:
        """Close the database connection engine."""
        if self.engine:
            logger.debug("Closing database engine.")
            await self.engine.dispose()
            self._initialized = False # Reset initialization status

    async def _ensure_initialized(self) -> None:
        """Ensure the database connection is initialized."""
        if not self._initialized:
            await self.initialize()

    async def save(self, task: Task) -> None:
        """Saves or updates a task in the database."""
        await self._ensure_initialized()

        task_data = task.model_dump() # Converts Pydantic Task to dict
        
        async with self.async_session_maker() as session:
            async with session.begin():
                stmt_select = select(TaskModel).where(TaskModel.id == task.id)
                result = await session.execute(stmt_select)
                existing_task_model = result.scalar_one_or_none()

                if existing_task_model:
                    logger.debug(f"Updating task {task.id} in the database.")
                    update_data = {
                        "contextId": task_data["contextId"],
                        "kind": task_data["kind"],
                        "status": task_data["status"], # Already a dict from model_dump
                        "artifacts": task_data.get("artifacts"), # Already a list of dicts
                        "history": task_data.get("history"), # Already a list of dicts
                        "metadata": task_data.get("metadata"), # Already a dict
                    }
                    stmt_update = update(TaskModel).where(TaskModel.id == task.id).values(**update_data)
                    await session.execute(stmt_update)
                else:
                    logger.debug(f"Saving new task {task.id} to the database.")
                    # Filter task_data to include only columns present in TaskModel
                    task_model_columns = {col.name for col in TaskModel.__table__.columns}
                    filtered_task_data = {k: v for k, v in task_data.items() if k in task_model_columns}
                    new_task_model = TaskModel(**filtered_task_data)
                    session.add(new_task_model)
                
                await session.commit()
        logger.info(f"Task {task.id} saved successfully.")

    async def get(self, task_id: str) -> Task | None:
        """Retrieves a task from the database by ID."""
        await self._ensure_initialized()

        async with self.async_session_maker() as session:
            stmt = select(TaskModel).where(TaskModel.id == task_id)
            result = await session.execute(stmt)
            task_model = result.scalar_one_or_none()

            if task_model:
                task_data_from_db = {
                    column.name: getattr(task_model, column.name)
                    for column in task_model.__table__.columns
                }
                # Pydantic's model_validate will parse the nested dicts/lists from JSON
                task = Task.model_validate(task_data_from_db)
                logger.debug(f"Task {task_id} retrieved successfully.")
                return task

            logger.debug(f"Task {task_id} not found in store.")
            return None

    async def delete(self, task_id: str) -> None:
        """Deletes a task from the database by ID."""
        await self._ensure_initialized()

        async with self.async_session_maker() as session:
            async with session.begin():
                stmt = delete(TaskModel).where(TaskModel.id == task_id)
                result = await session.execute(stmt)
                await session.commit()

                if result.rowcount > 0:
                    logger.info(f"Task {task_id} deleted successfully.")
                else:
                    logger.warning(
                        f"Attempted to delete nonexistent task with id: {task_id}"
                    )
