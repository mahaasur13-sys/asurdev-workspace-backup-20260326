"""
Sandbox Templates — базовые шаблоны для создания MicroVM.
"""
from .python_base import PYTHON_BASE_TEMPLATE
from .dockerfile import DOCKERFILE_TEMPLATE

__all__ = ["PYTHON_BASE_TEMPLATE", "DOCKERFILE_TEMPLATE"]
