# SOP Scenario Studio

Build small, explicit SOP evaluation worlds and simulate action traces against evidence, role, state and deadline gates. All service records are local JSON; the tool does not contact real ticketing, calendar, email or identity services.

## Quick start

Python 3.11+; no third-party runtime dependencies.

```bash
python -m pip install -e .
sop-studio validate examples/world.json
sop-studio build examples/world.json --output output/demo
sop-studio simulate examples/world.json examples/good-trace.json
sop-studio simulate examples/world.json examples/bad-trace.json
```

Use `python -m sop_studio` from a checkout without installing. The good trace accepts three actions and finishes in `scheduled`. The bad trace accepts two, rejects three and finishes in `approved`; its exit code is intentionally `1`.

## World format

See [the example](examples/world.json) and [contract](docs/scenario-contract.md).

| Collection | Role |
| --- | --- |
| `actors` | Stable IDs, display names and roles |
| `records` | Service, type, timestamp, author, body and links |
| `clauses` | SOP clause IDs and verbatim text |
| `workflow.initial_states` | Initial state for each existing target record |
| `workflow.transitions` | Allowed action/state changes and their gates |
| `absences` | Service/type combinations intentionally absent from the snapshot |

Every timestamp includes an offset and is compared as a UTC instant. Future evidence, dangling IDs, duplicate IDs, unknown clauses and contradictory absences are rejected. Similar display names never replace an actor ID.

Transitions cite a clause and specify an actor role. Optional evidence requirements match record type, author role and exact body values. Include a request ID in the requirement body to prevent using evidence from a different request. Optional prerequisite actions must have been accepted earlier for the same target. Deadlines are inclusive.

The simulator enforces the rules explicitly encoded in JSON. It does not derive policy logic from natural-language SOP text, infer a proposed booking date, assign accounts or send messages.

## Outputs

`build` preserves the supplied records and writes `world.json`, verbatim `SOP.md`, per-service projections under `services/`, a count budget, SHA-256 checksums and `scenario.zip`. The ZIP uses fixed timestamps and ordered members. Existing output directories are preserved.

`simulate` prints each decision, accepted/rejected status, before/after state, governing clause, rejection reasons and qualifying evidence IDs. Rejected actions do not change state. The input world and trace are never modified.

SOP Evidence Auditor can audit the resulting directory or ZIP and score traces against an observable rubric. Its standalone package carries the same interchange contract.

## Codex skill

This repository contains portable and Codex-compatible skills-only plugin manifests. Install the Python package before copying `skills/build-sop-scenario` into a client-supported skills location, or keep the complete repository as a local plugin source.

Use `$build-sop-scenario` to build and inspect a local world. The wrapper runs directly from a checkout:

```bash
python skills/build-sop-scenario/scripts/run.py build examples/world.json --output output/skill-demo
```

## Development

```bash
python -m unittest discover -s tests -v
python -m compileall -q sop_studio tests skills
```

CI covers Python 3.11, 3.12 and 3.13. Exit codes: `0` valid/completed without rejected actions, `1` completed simulation with rejected actions, `2` invalid input or operational failure.

[Reference notes](docs/reference-notes.md). MIT license.
