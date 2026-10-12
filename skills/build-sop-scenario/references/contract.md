# Scenario rules

Use schema version 1, stable actor IDs, offset timestamps and explicit links. Preserve snapshot evidence at or before the world clock. Keep declared service/type absences genuinely empty.

Represent each transition with an action, source state, destination state, actor role and existing SOP clause. Evidence requirements compare record type, author role and exact body values. Scope evidence to a request with body properties such as `request_id`.

Keep trace events chronological and at or after the snapshot clock. Rejected actions cannot advance state. Display names do not establish actor identity.

Read `docs/scenario-contract.md` at the complete plugin root for the full field contract. The wrapper requires the intact repository or an installed Python package.
