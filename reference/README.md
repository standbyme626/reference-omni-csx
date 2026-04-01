# Reference Codebases

This directory stores archived or external reference projects.

- `omni-csx-v35/`: legacy Omni-CSX repository snapshot used for analysis and migration reference.

Rules:

1. Do not use this directory as the primary runtime source.
2. Do not merge reference-only code to `main` as production path.
3. If code is promoted, copy selectively into canonical paths under `apps/*` and `providers/*`.
