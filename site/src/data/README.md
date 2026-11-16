# `src/data/`

Put sourced numbers and scenario tables here (JSON/TS). Calculators and charts
should import from this folder instead of hard-coding figures in components.

Example shape for a tool site:

```json
{
  "asOf": "2026-11-06",
  "defaults": {},
  "scenarios": {},
  "sources": []
}
```

Keep every figure with a source in docs or in the data file itself. Reader copy
still goes through `lint-copy` on build.
