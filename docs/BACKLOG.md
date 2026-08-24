# 🎯 Backlog Técnico & Plan de Mejora Continua — Myna

> **Motor**: Continuous Improvement Engine  
> **Modelo de Priorización**: RICE (Reach × Impact × Confidence / Effort)  
> **Última Actualización**: 24 de Agosto, 2026  

---

## 📊 Fórmula de Priorización RICE

$$\text{RICE Score} = \frac{\text{Reach (Alcance 1-10)} \times \text{Impact (Impacto 0.5-3)} \times \text{Confidence (Confianza %)}}{\text{Effort (Esfuerzo en Persona-Días)}}$$

- **Reach (1-10)**: Proporción de usuarios/solicitudes beneficiados.
- **Impact (0.5=Bajo, 1=Medio, 2=Alto, 3=Masivo)**: Incremento en valor, rendimiento o calidad.
- **Confidence (0.5 a 1.0)**: Certidumbre técnica en la solución.
- **Effort (Días)**: Tiempo estimado de implementación en días hábiles.

---

## 🏆 Top 10 Mejoras Priorizadas por ROI (RICE)

| ID | Título | Categoría | R | I | C | E | RICE Score | Tiempo Est. |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **FEAT-01** | Code-Splitting Plotly.js en Frontend | Rendimiento / UX | 10 | 3 | 1.0 | 1.0 | **30.0** | 1 día |
| **DEBT-01** | Limpieza de Archivo Huérfano `clean_nulls.py` | Deuda Técnica | 2 | 1 | 1.0 | 0.1 | **20.0** | 0.5 horas |
| **DEVOPS-01**| Integración de Sentry & Telemetría | DevOps / Observabilidad | 10 | 2 | 1.0 | 1.0 | **20.0** | 1 día |
| **FEAT-02** | Virtualización de Tabla (TanStack Table) | UX / Rendimiento | 10 | 3 | 0.9 | 1.5 | **18.0** | 1.5 días |
| **SEC-01**   | Rate Limiting & Sanitización de CSV | Seguridad | 10 | 2 | 0.9 | 1.5 | **12.0** | 1.5 días |
| **DOC-01**   | Especificación OpenAPI 3.1 & ADRs | Documentación | 6 | 2 | 1.0 | 1.0 | **12.0** | 1 día |
| **ARCH-01**  | Motor Analítico DuckDB en Core | Arquitectura | 9 | 3 | 0.9 | 2.0 | **12.15** | 2 días |
| **FEAT-03** | Procesamiento Asíncrono de Jobs | Arquitectura / UX | 8 | 3 | 0.9 | 2.0 | **10.8** | 2 días |
| **FEAT-04** | AI Analyst Agent (Gemini Flash API) | Feature / IA | 8 | 3 | 0.9 | 2.0 | **10.8** | 2 días |
| **ARCH-02**  | Adaptador S3 Remote Storage | Arquitectura | 7 | 3 | 0.9 | 2.0 | **9.45** | 2 días |

---

## 📋 Sub-Backlogs Especializados

### 📦 Product Backlog (Funcionalidades de Usuario)
1. **FEAT-01**: Carga perezosa (Code-Splitting) de componentes de visualización Plotly.
2. **FEAT-02**: Tabla virtualizada para navegación a 60 FPS sobre 100,000+ filas.
3. **FEAT-04**: AI Agent Data Analyst usando Gemini Flash API para resúmenes ejecutivos.
4. **FEAT-05**: Exportación de reportes ejecutivos en PDF y HTML interactivo.
5. **FEAT-06**: Autenticación multi-tenant y Workspaces compartidos (Supabase Auth).

### 🛠️ Technical Backlog (Infraestructura & Refactor)
1. **ARCH-01**: Integración de DuckDB en `StatisticalAnalyzer` para consultas SQL vectorizadas.
2. **FEAT-03**: Sistema de colas de procesamiento asíncrono (`202 Accepted` + Polling).
3. **ARCH-02**: Implementación de `S3DataRepository` para almacenamiento remoto.
4. **SEC-01**: Rate limiting por IP/API-Key y sanitización de fórmulas en exportaciones.

### 🏛️ Architectural Backlog (Diseño de Dominio & Puertos)
1. **ARCH-01**: Adopción de DuckDB como motor analítico sin romper el puerto `core/ports.py`.
2. **ARCH-02**: Desacoplamiento total del estado de sesión efímero mediante `StorageProvider`.
3. **ARCH-03**: Introducción de Enums fuertemente tipados (`CleaningMethodEnum`, `ScalingMethodEnum`) en reemplazo de strings mágicos.

### 💳 Debt Backlog (Deuda Técnica)
1. **DEBT-01**: Eliminación del módulo huérfano legacy `clean_nulls.py`.
2. **DEBT-02**: Sustitución de respuestas `dict` genéricas en skills por modelos Pydantic.
3. **DEBT-03**: Reemplazo de la re-transmisión masiva de `df_json` en el cliente React.

---

## 🗺️ Roadmap de Versiones

### 🚀 Version 0.3.0 — Performance & Stability (Sprint 1)
- Code-Splitting de Plotly.js en Frontend.
- Previsualización de tabla virtualizada con `@tanstack/react-table`.
- Integración de Sentry APM y endpoints `/healthz`/`/readyz`.
- Eliminación de deuda técnica huérfana (`clean_nulls.py`).

### 🚀 Version 0.4.0 — High-Volume Analytics (Sprint 2)
- Motor analítico DuckDB integrado en el Core.
- Procesamiento asíncrono por polling (`/api/jobs/{id}`).
- Adaptador remoto `S3DataRepository`.

### 🚀 Version 1.0.0 — AI & Executive Reporting (Sprint 3)
- AI Analyst Agent con la API de Gemini.
- Exportación de reportes ejecutivos en PDF / HTML.
- Especificación OpenAPI 3.1 completa en `/docs`.

### 🚀 Version 1.1.0 — Enterprise Security & Multi-tenancy
- Autenticación Multi-tenant con Supabase Auth.
- Rate limiting y sanitización estricta de entradas.
