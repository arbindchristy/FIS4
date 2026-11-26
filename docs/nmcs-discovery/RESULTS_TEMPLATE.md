# Sanitized discovery report

Operator approval reference (sanitized): ___
Run state: NOT RUN / PASS / BLOCK
Connection/authentication, read-only privileges, TLS and bounded plan verified:
___ (status only; omit addresses and credentials)

| Logical field | Mapping attested locally? | Safe type family / nullable? | Open semantic question |
|---|---|---|---|
| Observation timestamp and availability | | | |
| Stable aircraft key and tail | | | |
| Raw-to-canonical status incl. ambiguous PMC | | | |
| Historical command and platform | | | |
| Inspection and phase hours, defaults and availability | | | |

| Aggregate (approved coarse or suppressed only) | Result | PASS / BLOCK / NOT RUN |
|---|---|---|
| Window length and row budget, cap status | | |
| Observed day coverage and missing working-day ranges | | |
| Rows and distinct aircraft | | |
| Canonical status distribution, null and unmapped buckets | | |
| Duplicate key groups and extra rows | | |
| Null key/status counts; timestamp nullability audit status | | |

Record permission/metadata gaps, known gaps in the active roster and calendar,
correction and availability semantics, identity reuse, intraday tie-breakers,
carry limits, historical assignment provenance and hours defaults: ___

Disposition and unresolved blockers: ___. PASS covers discovery only. Attach
no definitions, physical mapping names, raw status codes, exact operational
dates/counts, tail identifiers or raw outputs to Git or ChatGPT.
