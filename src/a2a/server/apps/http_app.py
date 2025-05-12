from abc import ABC, abstractmethod
from starlette.applications import Starlette

class HttpApp(ABC):

  @abstractmethod
  def build(self, **kwargs) -> Starlette:
    pass
