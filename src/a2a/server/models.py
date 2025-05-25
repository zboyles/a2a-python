from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB # For PostgreSQL specific JSON type, can be generic JSON too

Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    contextId = Column(String, nullable=False)
    kind = Column(String, nullable=False, default='task')
    
    # Storing Pydantic models as JSONB for flexibility
    # SQLAlchemy's JSON type is generally fine, JSONB is a PostgreSQL optimization
    # For broader compatibility, we might stick to JSON or use a custom type if needed.
    status = Column(JSONB)  # Stores TaskStatus as JSON
    artifacts = Column(JSONB, nullable=True)  # Stores list[Artifact] as JSON
    history = Column(JSONB, nullable=True)  # Stores list[Message] as JSON
    metadata = Column(JSONB, nullable=True) # Stores dict[str, Any] as JSON

    def __repr__(self):
        return f"<TaskModel(id='{self.id}', contextId='{self.contextId}', status='{self.status}')>"
