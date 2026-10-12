---
name: build-sop-scenario
description: Build and simulate local SOP evaluation scenarios from explicit JSON worlds. Use when creating mock service records, preserving declared absences, checking cross-record links or testing role, evidence, state and timing gates.
---

# Build an SOP scenario

Read [the scenario rules](references/contract.md). Keep supplied clock, actors, records, values and absences intact unless the user requests a change. Record SOP text separately from the rules encoded in the workflow.

1. Resolve the world JSON and a new output directory.
2. Run `python <skill-directory>/scripts/run.py validate <world>`.
3. Run `python <skill-directory>/scripts/run.py build <world> --output <new-directory>`.
4. Inspect `budget.json`, service projections and verbatim SOP clauses.
5. When a trace is provided, run `python <skill-directory>/scripts/run.py simulate <world> <trace>`.
6. Report accepted and rejected actions, final states, clauses and evidence IDs. Treat exit code 1 as a completed simulation containing rejected actions.

Do not add missing evidence merely to make a trace pass. Do not interpret simulated acceptance as permission to act on a real external service. Identify policies the encoded rules do not cover.
