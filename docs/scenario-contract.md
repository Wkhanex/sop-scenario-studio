# Scenario contract

The world has schema version 1 and a lowercase scenario ID. Actors, records and clauses have unique safe IDs within their collections; record and clause IDs also cannot overlap. Records contain `service`, `type`, offset timestamp `at`, `actor_id`, object `body` and optional `refs` to existing records.

All records are snapshot evidence at or before `clock`. The workflow maps record IDs to initial states and declares transitions with `action`, `from`, `to`, `role` and `clause`. Each action/from pair is unique.

An evidence requirement declares a `type`, optional author `role`, and optional exact `body` properties. Comparison includes JSON value types: `true` does not equal `1`. Body requirements are literal values, with no expressions or variable substitution. A single record may satisfy multiple requirements where appropriate.

`requires_actions` lists known action names. Each must have been accepted for the same target earlier in the trace. A transition's optional `deadline` is inclusive and must include an offset.

A trace contains `events`. Each event has a unique `id`, `action`, `actor_id`, existing workflow `target_id`, offset timestamp `at` and optional distinct `evidence_ids`. Events are supplied in chronological order, all at or after the world clock. Unknown actions are recorded as rejected decisions; unknown actors, targets or evidence IDs invalidate the trace.

The tool is a workflow gate simulator. It does not inspect proposed booking details or infer contractual compliance from prose. Add explicit rules or extend the model before using it to test another kind of policy.

Local JSON is an author-controlled interchange format, not a replica of a hosted service loader. The repository has no automatic migration or platform-specific adapter.
