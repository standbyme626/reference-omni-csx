# Repository Reorganization Checklist

## Goal

Reorganize this branch into a middleware-first workspace, isolate simulation as microservices, and archive legacy reference code without polluting `main`.

## Checklist

- [x] Define canonical workspace and transition rules (`WORKSPACE.md`)
- [x] Create canonical directories: `apps/core`, `apps/sim`, `apps/frontend`, `reference`
- [x] Move middleware services into canonical `apps/core/*`
- [x] Move simulation services into canonical `apps/sim/*`
- [x] Archive legacy monorepo under `reference/*`
- [x] Add compatibility symlinks for old paths
- [x] Update key config/docs to canonical paths
- [x] Validate key paths and health commands
- [x] Fix `user-sim-service -> official-sim-server` contract mismatches (health path + configurable base URL + query API fallback)
- [x] Fix Odoo integration empty-list issue (support list queries in provider + service)
- [x] Add compatibility alias: `/official-sim/query/*` -> raw query routes
- [x] Add branch/main isolation analysis doc (`docs/branch-main-analysis.md`)
- [x] Add boundary READMEs for `apps/core`, `apps/sim`, `apps/frontend`
- [x] Convert `apps/frontend/conversation-studio-web` from empty shell to linked entry (points to user-sim static page)
- [x] Clean runtime artifacts in repo tree (`.pytest_cache`, `.ruff_cache`, `official_sim.db`)

## Execution Notes

- Migration strategy: **non-destructive first** (move + symlink compatibility).
- Branch safety: keep changes in feature branch; no direct merge to `main` until CI + contract checks pass.
- Runtime alignment:
  - `official-sim-server` default API still on `:8000` (health: `/healthz`)
  - `user-sim-service` default runtime moved to `:8001` (`USER_SIM_PORT` 可覆盖)
  - `OFFICIAL_SIM_BASE_URL` 可显式指定 user-sim 连接目标
