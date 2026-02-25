# Agent — DataPrepAgent (Agente Generalista)

## Propósito

`DataPrepAgent` es el **único agente orquestador** del sistema. Coordina la ejecución de `skills` (acciones atómicas) sobre una `AnalysisSession`. Su responsabilidad es planificar, validar, ejecutar y persistir el resultado de una secuencia de skills.

> **Principio de densidad**: No se crean agentes especializados adicionales (CleanerAgent, StatsAgent, etc.). Si una nueva skill encaja en el dominio de datos (I/O, limpieza, transformación, estadística, ML, visualización), se registra en este agente mediante `@register_skill`.

## Arquitectura

```
Client → API (router) → AgentManager.execute_skill(...) → Skill → Domain Services → Repos
```

- `AgentManager` es el dispatcher: recibe un `skill_id` y los `**kwargs`, valida, ejecuta y devuelve `SkillResult`.
- El router **NO** debe llamar a `domain_services` directamente; siempre delega en `AgentManager`.

## Modelos y contratos

- `AnalysisSession` (ver `src/core/models.py`): contiene `current_df` y `logs`.
- Firma esperada para skills: `skill(session: AnalysisSession, **kwargs) -> dict | SkillResult`

## Ciclo de vida de una petición

1. Cliente envía petición (p. ej. `/api/clean/nulls`).
2. Router obtiene `AnalysisSession` via `Depends(get_analysis_session)`.
3. Router llama a `agent_manager.execute_skill("clean_nulls", session, columns=[...], method="...")`.
4. `AgentManager` valida, ejecuta la skill registrada y devuelve `SkillResult`.
5. Router persiste `AnalysisSession` y devuelve respuesta al cliente.

## Skills registradas en DataPrepAgent

| skill_id             | Grupo         | Archivo de implementación                        |
|----------------------|---------------|--------------------------------------------------|
| `load_file`          | I/O           | `src/core/agents/skills/io_skills.py`            |
| `export_file`        | I/O           | `src/core/agents/skills/io_skills.py`            |
| `clean_nulls`        | Cleaning      | `src/core/agents/skills/clean_skills.py`         |
| `drop_duplicates`    | Cleaning      | `src/core/agents/skills/clean_skills.py`         |
| `scale_columns`      | Transform     | `src/core/agents/skills/transform_skills.py`     |
| `encode_categoricals`| Transform     | `src/core/agents/skills/transform_skills.py`     |
| `compute_stats`      | Stats         | `src/core/agents/skills/stats_skills.py`         |
| `kmeans_cluster`     | ML            | `src/core/agents/skills/ml_skills.py`            |
| `plot`               | Visualization | `src/core/agents/skills/visualization_skills.py` |

## Trazabilidad y versionado

- `AnalysisSession` debe extenderse con `skill_history: List[dict]` (ver BACKLOG).
- Cada skill debe anotar su ejecución con `skill_id`, `params`, `timestamp` y `result_summary`.

## Extensibilidad

- Para añadir una nueva skill: implementar la función con `@register_skill("nuevo_id")` en el archivo de grupo correspondiente e importarla en `dependencies.py`.
- `AgentManager` puede implementar hooks pre/post (validación, métricas, tracing) sin modificar las skills individuales.

## Operación y despliegue

- En entornos serverless (Vercel) evitar estado local compartido; usar S3/DB para `current_df`/artifacts (ver BACKLOG).
- Documentar límites: uso de `/tmp` en Vercel y concurrencia limitada.

## Referencias

- `src/core/models.py` — `AnalysisSession`
- `src/core/agents/base.py` — `AgentManager`, `SkillResult`, `register_skill`
- `src/adapters/api/dependencies.py` — carga/guardado de sesión y singleton de `AgentManager`
- `src/core/domain_services.py` — servicios de dominio que usan las skills
