# Workspace Layout (Canonical)

## Principles

- `main` must stay clean; no mixed delivery of two unrelated systems.
- Customer-service middleware (`中台`) is the primary runtime.
- Simulation is a support subsystem, implemented as independent services.
- Legacy Omni-CSX codebase is reference-only and must not drive release builds directly.

## Canonical Top-Level Structure

- `apps/core/*`: middleware core services
- `apps/sim/*`: simulation services
- `apps/frontend/*`: frontend applications
- `providers/*`: platform provider layer
- `artifacts/*`: generated runtime/build artifacts
- `data/raw|processed|staging/*`: dataset lifecycle
- `reference/*`: archived/legacy/reference codebases
- `docs/*`: architecture, specs, and delivery docs

## Simulation Service Split

- `apps/sim/official-sim-server`: simulate official platform APIs/webhooks/callbacks
- `apps/sim/user-sim-service`: simulate user behavior / conversation turns

## Frontend Transition

- `apps/frontend/conversation-studio-web` is the canonical frontend location.
- Current page content is aligned with `apps/sim/user-sim-service/static/conversation_studio.html` for transition compatibility.
