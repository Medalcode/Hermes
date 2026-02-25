# Skills — Catálogo y convenciones

## ¿Qué es una Skill?

Una `Skill` es una acción atómica y reutilizable que opera sobre una `AnalysisSession`. Debe ser stateless y, de preferencia, idempotente. Todas las skills se agrupan en **archivos de grupo** (Super-Skills paramétricas); no se crea un archivo `.py` por cada skill individual.

> **Principio de reutilización**: Antes de crear una nueva skill, verifica si una existente puede recibir un parámetro extra (`method`, `type`, `stat_type`) para hacer lo mismo. Solo si la lógica diverge significativamente (>20%) se justifica un archivo separado.

## Convenciones de implementación

- Firma recomendada: `skill(session: AnalysisSession, **kwargs) -> dict | SkillResult`
- `SkillResult`: `{ "changes": {...}, "preview": {...}, "logs": [...] }`
- Toda skill debe llamar a `session.add_log(...)` para trazabilidad.
- Registro: `@register_skill("skill_id", description="...")` en el archivo de grupo.

## Catálogo de Super-Skills (agrupadas por archivo)

---

### 📁 `src/core/agents/skills/io_skills.py`

#### `load_file`
```
skill_id:  load_file
signature: load_file(session, file_obj, delimiter=",") -> dict
outputs:   { columns, numeric_columns, preview, shape }
delega en: FileSystemAdapter.load_file()
```

#### `export_file`
```
skill_id:  export_file
signature: export_file(session, format_type="CSV") -> dict
outputs:   { file_path }
delega en: FileSystemAdapter.export_file()
parámetro: format_type ∈ {"CSV", "Excel"}
```
> `load_file` y `export_file` comparten el mismo adaptador. Ambas viven en el mismo archivo.

---

### 📁 `src/core/agents/skills/clean_skills.py`

#### `clean_nulls`
```
skill_id:  clean_nulls
signature: clean_nulls(session, columns: List[str], method: str) -> dict
outputs:   { preview, affected_count }
delega en: DataCleaner.handle_nulls()
parámetro: method ∈ {"Eliminar filas", "Llenar con promedio", "Llenar con mediana", ...}
```

#### `drop_duplicates`
```
skill_id:  drop_duplicates
signature: drop_duplicates(session, subset: List[str] = None) -> dict
outputs:   { preview, affected_count }
delega en: pd.DataFrame.drop_duplicates()
```
> `clean_nulls` y `drop_duplicates` son operaciones de limpieza; viven juntas. No se usa `method` como discriminador porque sus firmas divergen en el parámetro `subset` vs `columns`.

---

### 📁 `src/core/agents/skills/transform_skills.py`

#### `scale_columns`
```
skill_id:  scale_columns
signature: scale_columns(session, columns: List[str], method: str) -> dict
outputs:   { preview }
delega en: DataScaler.apply_scaling()
parámetro: method ∈ {"Min-Max", "Z-Score"}
```

#### `encode_categoricals`
```
skill_id:  encode_categoricals
signature: encode_categoricals(session, columns: List[str], method: str = "one-hot") -> dict
outputs:   { preview, new_columns }
delega en: pd.get_dummies() (one-hot) | pd.factorize() (label)
parámetro: method ∈ {"one-hot", "label"}
```
> Ambas son transformaciones de columnas. Viven juntas. Comparten la guardia `session.has_data()`.

---

### 📁 `src/core/agents/skills/stats_skills.py`

#### `compute_stats` ← **Super-Skill paramétrica** (fusión de `compute_descriptive` + `compute_correlation`)
```
skill_id:  compute_stats
signature: compute_stats(session, stat_type: str) -> dict
outputs:   { result }
delega en: StatisticalAnalyzer.calculate_descriptive_stats() | calculate_correlation_matrix()
parámetro: stat_type ∈ {"descriptive", "correlation", "distribution_shape"}
```
> **Línea de fusión**: `compute_descriptive` y `compute_correlation` comparten el 90% de la lógica (guardia de datos, instanciar `StatisticalAnalyzer`, retornar dict). Se unifican con un único parámetro `stat_type`. No se crean dos archivos separados.

---

### 📁 `src/core/agents/skills/ml_skills.py`

#### `kmeans_cluster`
```
skill_id:  kmeans_cluster
signature: kmeans_cluster(session, columns: List[str], k: int = 3) -> dict
outputs:   { preview, message }
delega en: Clusterer.kmeans()
```

---

### 📁 `src/core/agents/skills/visualization_skills.py`

#### `plot` ← **Super-Skill paramétrica** (fusión de `plot_distribution` + `plot_correlation` + `plot_regression` + `plot_clusters`)
```
skill_id:  plot
signature: plot(session, type: str, col: str = None, x: str = None, y: str = None) -> dict
outputs:   { figure_json }
delega en: PlottingAdapter.*
parámetro: type ∈ {"distribution", "correlation", "regression", "cluster"}
```
> **Línea de fusión**: Las 4 funciones de plotting comparten el 85% de la lógica (guardia de datos, llamar a `PlottingAdapter`, serializar `fig.to_json()`). Se unifican en una sola skill con `type` como discriminador. Mismo patrón que el endpoint `/api/plot` de `router.py`.

---

## Archivos de implementación de skills

| Archivo                         | Skills contenidas                            |
|---------------------------------|----------------------------------------------|
| `io_skills.py`                  | `load_file`, `export_file`                   |
| `clean_skills.py`               | `clean_nulls`, `drop_duplicates`             |
| `transform_skills.py`           | `scale_columns`, `encode_categoricals`       |
| `stats_skills.py`               | `compute_stats`                              |
| `ml_skills.py`                  | `kmeans_cluster`                             |
| `visualization_skills.py`       | `plot`                                       |

## Archivos huérfanos / obsoletos tras la consolidación

| Archivo                                    | Estado    | Acción recomendada                          |
|--------------------------------------------|-----------|---------------------------------------------|
| `src/core/agents/skills/clean_nulls.py`    | ⚠️ Huérfano | **Eliminar** — su lógica migra a `clean_skills.py` |

## Cómo conectar las skills al router

El `router.py` **NO debe llamar directamente** a `domain_services`. Debe delegar en `AgentManager`:

```python
# ❌ Actual (bypass del AgentManager)
df_new, count = DataCleaner.handle_nulls(session.current_df, cols, method)

# ✅ Correcto
result = agent_manager.execute_skill("clean_nulls", session, columns=cols, method=method)
```

> Importar `agent_manager` desde `src/adapters/api/dependencies.py` mediante `Depends(get_agent_manager)`.

## Buenas prácticas

- Mantener efectos laterales explícitos (modificar `session.current_df` deliberadamente).
- Añadir pruebas unitarias para cada skill (mock de `AnalysisSession`).
- Registrar `skill_history` en la sesión para permitir auditoría y rollback (ver BACKLOG).

## Referencias

- Registro / manager: `src/core/agents/base.py`
- Adaptador de archivos: `src/adapters/fs/file_io.py`
- Adaptador de visualización: `src/adapters/visualization/plotter.py`
- Servicios de dominio: `src/core/domain_services.py`
