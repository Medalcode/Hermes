# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-24

### Added
- **Hexagonal Architecture Core Ports**: Added `FileIOProvider` and `PlotterProvider` abstract ports to `src/core/ports.py` to enforce strict hexagonal layer isolation.
- **Outlier Handling Skill**: Registered `@register_skill("handle_outliers")` in `clean_skills.py` for IQR detection, removal, and Winsorization capping.
- **Extended Test Suite**: Added 32 new tests across `tests/test_skills.py`, `tests/test_domain_services_edge_cases.py`, and `tests/test_api_edge_cases.py`, increasing test count from 21 to 53 passing tests and test coverage to 88%.
- **GitHub Actions CI Pipeline**: Created `.github/workflows/ci.yml` running Python 3.11 linting (Ruff), type checking (Mypy), test coverage (Pytest), and Node.js 20 frontend builds.
- **Global Pytest Initialization**: Added `tests/conftest.py` and `src/core/agents/skills/__init__.py` for automatic skill registration upon package import.

### Changed
- **Strict Layer Isolation**: Removed all infrastructure imports (`src.adapters.*`) from core skills (`io_skills.py`, `visualization_skills.py`), replacing them with dynamic dependency resolution via core provider ports.
- **Router Consolidation**: Refactored `/api/outliers` and `/api/plot` endpoints in `src/adapters/api/router.py` to delegate execution through `agent_manager.execute_skill(...)`.
- **Payload Extraction Refactoring**: Added `_prepare_session_dataframe` helper in `src/adapters/api/router.py` to remove duplicate session extraction logic across endpoints.
- **Statsmodels Fallback**: Added robust linear regression fallback in `PlottingAdapter.plot_regression` when `statsmodels` is omitted or uninstalled.
- **Code Quality & Type Annotations**: Fixed all Ruff linting warnings and updated Mypy configuration in `pyproject.toml` with clean strict compliance.

### Fixed
- Fixed Vercel stateless execution payload extraction for `/api/clean/nulls` and `/api/clean/scale`.
- Fixed Vercel `/tmp` export path handling in `FileSystemAdapter.export_file`.

## [0.1.0] - 2026-08-04

### Added
- Initial Vercel serverless deployment setup with FastAPI backend and React frontend.
- Native NumPy implementations for K-Means clustering, Z-Score scaling, and Kurtosis distribution shape calculations.
- AgentManager orchestration and 9 super-skills system.
