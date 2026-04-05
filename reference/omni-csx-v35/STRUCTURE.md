# Omni-CSX v3.5 Reference Structure

This directory is a **reference snapshot** inside platform-sim.

## Canonical top-level directories

- `apps/`: runtime services and frontend apps
- `packages/`: shared libraries
- `providers/`: platform provider implementations
- `infra/`: docker, migrations, ops scripts
- `scripts/`: operational scripts
- `tests/`: test suites
- `docs/`: documentation
- `.ai/`: agent planning/version artifacts

## Cleanup decisions

- Root loose scripts moved to `scripts/maintenance/`.
- Root loose test files moved to `tests/legacy/`.
- Root loose note moved to `docs/archive/notes/`.
- Build artifacts removed:
  - `node_modules/`
  - `apps/agent-console/.next/`
  - `apps/agent-console/node_modules/`

## Notes

- `agent.md` stays at root as repository-level instruction entry.
- Reinstall JS dependencies when needed: `pnpm install`.
