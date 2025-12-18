# 🐦 Myna — Intelligent Data Mining Platform
[![CI](https://github.com/Medalcode/Myna/actions/workflows/ci.yml/badge.svg)](https://github.com/Medalcode/Myna/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Myna es una plataforma de data mining para exploración, limpieza y análisis estadístico de datasets tabulares. Construida con **Arquitectura Hexagonal** y **sistema Agent/Skill** y desplegada en Vercel como API serverless.

No es un script experimental: es un sistema diseñado para crecer en reglas de negocio, algoritmos y usuarios, manteniendo testabilidad y separación estricta de responsabilidades.

---

## 🎯 Problema que resuelve

En entornos analíticos típicos:
- Los flujos de análisis viven en notebooks frágiles o scripts monolíticos.
- La lógica de negocio se mezcla con UI, I/O y visualización.
- Escalar a múltiples datasets, sesiones o algoritmos implica reescribir todo.

Myna ataca ese problema desde la **arquitectura**, no desde el tooling.

---

## ✨ Capacidades

### 📊 Análisis y preparación de datos
- Estadística descriptiva (media, mediana, std, curtosis, asimetría)
- Tratamiento de valores nulos: media, mediana, moda, cero, eliminación de filas
- Eliminación de duplicados
- Escalado: Min-Max y Z-Score
- Codificación de categóricas: one-hot y label encoding
- Detección y tratamiento de outliers (IQR: informar, eliminar, winsorización)

### 🤖 Aprendizaje no supervisado
- K-Means clustering (implementación nativa NumPy, sin scikit-learn)

### 📈 Visualización interactiva (Plotly.js)
- Mapa de calor de correlaciones
- Histograma de distribución con boxplot marginal
- Regresión lineal (scatter + trendline)
- Clusters coloreados

---

## 🏗️ Arquitectura

```
Myna/
├── api/
│   └── index.py                  ← Entrypoint Vercel (importa FastAPI app)
│
├── src/
│   ├── main.py                   ← Entrypoint local (uvicorn)
│   │
│   ├── core/                     ← Dominio puro (sin frameworks)
│   │   ├── models.py             ← AnalysisSession, OperationLog
│   │   ├── ports.py              ← Interfaces ABC (SessionRepository, DataRepository)
│   │   ├── domain_services.py   ← Lógica de negocio: StatisticalAnalyzer, DataCleaner,
│   │   │                            DataScaler, OutlierManager, Clusterer
│   │   └── agents/
│   │       ├── base.py           ← AgentManager, SkillResult, @register_skill
│   │       └── skills/           ← 9 Super-Skills paramétricas (6 archivos)
│   │           ├── io_skills.py              → load_file, export_file
│   │           ├── clean_skills.py           → clean_nulls, drop_duplicates
│   │           ├── transform_skills.py       → scale_columns, encode_categoricals
│   │           ├── stats_skills.py           → compute_stats (descriptive|correlation|shape)
│   │           ├── ml_skills.py              → kmeans_cluster
│   │           └── visualization_skills.py   → plot (distribution|correlation|regression|cluster)
│   │
│   └── adapters/                 ← Infraestructura (dependen del core, nunca al revés)
│   ├── api/
│   │   ├── router.py         ← 10 endpoints REST que usan AgentManager.execute_skill()
│   │   └── dependencies.py   ← DI: sesión, AgentManager, registro de skills
│       ├── fs/
│       │   └── file_io.py        ← Carga/exportación de archivos (CSV, Excel)
│       ├── repositories/
│       │   └── local_storage.py  ← Persistencia local/tmp (LocalFile*Repository)
│       └── visualization/
│           └── plotter.py        ← PlottingAdapter (Plotly)
│
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   └── index.html
│
├── tests/
│   ├── test_core_services.py   ← 8 tests de dominio
│   └── test_api.py             ← 11 tests de integración API (TestClient)
│
└── docs/
    ├── agent.md      ← Arquitectura del AgentManager y DataPrepAgent
    ├── skills.md     ← Catálogo de Super-Skills, convenciones, fusiones
    └── BACKLOG.md    ← Roadmap técnico priorizado
```

### Regla fundamental

> El dominio no conoce a FastAPI, Plotly ni al filesystem.  
> Los adapters dependen del core, **nunca al revés**.

---

## 🤖 Agent & Skills (capa de orquestación)

Myna implementa un sistema de `Agent` / `Skill` para pipelines reproducibles y extensibles:

- **`DataPrepAgent`** — único agente orquestador del sistema. Coordina todas las skills sobre una `AnalysisSession` via `AgentManager`.
- **`Skill`** — acción atómica registrada con `@register_skill`. Recibe `session` + parámetros, delega en `domain_services` y devuelve `SkillResult`.
- **Super-Skills paramétricas** — en lugar de un archivo por skill, las skills con lógica similar se agrupan en un único archivo con un parámetro discriminador (e.g. `compute_stats(stat_type=...)`, `plot(type=...)`).

Ver documentación detallada en [`docs/agent.md`](docs/agent.md) y [`docs/skills.md`](docs/skills.md).

---

## ⚖️ Decisiones de Arquitectura (ADR)

### 1. Optimización Zero-Dependencies (Vercel 250MB limit)
- `scikit-learn` y `scipy` exceden el límite de Serverless Functions en Vercel.
- **Solución**: K-Means, Z-Score y Kurtosis implementados con NumPy puro. Artefacto final < 100MB.

### 2. Persistencia agnóstica
- `ports.py` define interfaces (`SessionRepository`, `DataRepository`).
- Implementación actual: `LocalFileSessionRepository` + `LocalFileDataRepository` (archivos JSON + Pickle).
- Migrar a S3 o Redis requiere solo implementar los ports y cambiar la inyección en `dependencies.py`.

### 3. Visualización desacoplada
- El backend genera JSON de Plotly. Cualquier frontend puede renderizarlo sin lógica de negocio en el cliente.

### 4. Sesiones multi-usuario con cookies
- Cada request lleva un `session_id` en cookie. Sin estado global compartido.

### 5. Modos de ejecución de sesión
- **Local Dev (no Vercel)**: estado server-side por cookie + persistencia en `storage/` (metadata JSON + DataFrame en pickle).
- **Vercel Stateless (`VERCEL=1`)**: el backend no persiste sesión; el frontend guarda estado en IndexedDB y envía `df_json` (`DataFrame.to_json(orient="split")`) en cada operación.

---

## 🧪 Testing

```bash
PYTHONPATH=. pytest tests/ -v
```

Los tests cubren comportamiento de dominio (sin mocks de frameworks). Esto permite refactors estructurales sin romper la lógica central.

## 🔐 API Key Authentication

Opcional: define `MYNA_API_KEY` en el entorno para requerir autenticación en todos los endpoints `/api/`. Los clientes deben incluir el header `X-API-Key: <tu-api-key>` en cada request. Sin la variable de entorno, la API funciona sin autenticación.

---

## ▶️ Ejecución local

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python src/main.py
```

Abrir en el navegador: **http://localhost:8000**

---

## 🔄 Historial de versiones

| Versión | Cambios principales |
|---|---|
| **V6.1** | Vercel stateless mode (df_json + IndexedDB) + AgentManager router (08/04/2026) |
| **V6.0** | Super-Skills paramétricas, AgentManager integrado, eliminación de código legacy (Gradio) |
| **V5.1** | Repository Pattern, soporte multi-sesión con cookies |
| **V5.0** | Migración completa a FastAPI + UI custom, Arquitectura Hexagonal |
| **V4.0** | Modularización inicial (Gradio) |
| Legacy | Script monolítico `final_eval3mineria.py` |

---

## 🧭 Roadmap

Ver [`docs/BACKLOG.md`](docs/BACKLOG.md) para el plan técnico priorizado. Próximos hitos:

- [ ] Adaptador S3 para persistencia real en producción
- [ ] Patrón Strategy para limpieza y escalado (eliminar `if/else` de strings mágicos)
- [x] Test de integración end-to-end (Upload → Clean → Scale → Cluster → Outliers → Export → Dedup)
- [ ] Manejo asíncrono de operaciones pesadas (Job Queue)
- [x] Router refactorizado: todos los endpoints usan AgentManager.execute_skill()
- [x] Endpoints nuevos: `/api/outliers`, `/api/clean/dedup`, `/api/export`
- [x] Stats endpoint retorna JSON estructurado en vez de Markdown
- [x] FileSystemAdapter acepta BytesIO in-memory (fix upload vía FastAPI)
- [x] API Key authentication middleware (optional, via `MYNA_API_KEY` env var)
- [x] CI/CD pipeline (ruff linting + pytest)
- [x] Tests badge en README

---

_Created by [Medalcode](https://github.com/Medalcode)_
