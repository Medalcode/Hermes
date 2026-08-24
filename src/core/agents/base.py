from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.core.models import AnalysisSession


@dataclass
class SkillResult:
    changes: dict[str, Any]
    preview: dict[str, Any] | None = None
    logs: list | None = None


# Simple registry (in-memory). Skills se registran con el decorador `@register_skill`.
_SKILL_REGISTRY: dict[str, dict[str, Any]] = {}


def register_skill(skill_id: str, description: str = "") -> Callable:
    def decorator(fn: Callable):
        _SKILL_REGISTRY[skill_id] = {"func": fn, "description": description}
        return fn

    return decorator


class AgentManager:
    """Manager ligero para registrar y ejecutar skills por nombre.

    Uso inicial: instanciar un singleton en `src/adapters/api/dependencies.py` y usar
    `agent_manager.execute_skill(skill_id, session, **params)` desde rutas o agentes.
    """

    def __init__(self) -> None:
        import src.core.agents.skills  # noqa: F401

        self._registry = _SKILL_REGISTRY


    def register(self, skill_id: str, func: Callable, description: str = "") -> None:
        self._registry[skill_id] = {"func": func, "description": description}

    def list_skills(self):
        return list(self._registry.keys())

    def execute_skill(self, skill_id: str, session: AnalysisSession, **kwargs) -> SkillResult:
        if skill_id not in self._registry:
            raise KeyError(f"Skill '{skill_id}' no encontrada en el registro")

        fn = self._registry[skill_id]["func"]

        # Ejecutar la función de la skill; se espera que modifique `session` si corresponde
        result = fn(session, **kwargs)

        if isinstance(result, SkillResult):
            return result
        if isinstance(result, dict):
            return SkillResult(
                changes=result, preview=result.get("preview"), logs=result.get("logs", [])
            )

        # Resultados no standard
        return SkillResult(changes={"result": result})
