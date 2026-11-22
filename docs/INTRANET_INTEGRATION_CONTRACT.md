# Intranet integration contract

Status: Phase 03C-0 documentation approved by the chief architect on 2026-11-22.
Prediction compatibility, physical SQL verification and deployment acceptance remain unverified.
Recorded 2026-11-22. Read [Streamlit parity](STREAMLIT_PARITY.md),
[decisions](DECISIONS.md) and [release gates](RELEASE_GATES.md) together.
This is a logical contract, not SQL DDL or an implemented integration.

## Source boundary

The customer-designated source is the existing `VW_MNT_AIRCRAFT_HISTORY` view.
Leave its definition, joins and active-aircraft filtering unchanged. It attributes
history using current aircraft/organizational assignments. Do not replace it with
a current-serviceability source, introduce a mandatory new view, filter away
unchanged-status reports, or invent historical assignments.

No database was contacted. Exact physical names/types, nullability, timezone,
permissions and cardinality need approved sanitized evidence. No schema qualifier,
server/database address, credentials, real unit mapping, production records or
restricted definition belongs in this repository.

## Logical observation projection

Names below are application aliases, not assertions about physical SQL columns.
The adapter maps the unchanged view's verified fields to these aliases.

| Logical field | Meaning and compatibility requirement |
|---|---|
| `date` | Observation timestamp; preserve precision/order until daily collapse; verify timezone/calendar convention |
| `platform` | Text aircraft platform attribute; retain verified command association independently of hierarchy |
| `tail` | Text identifier from ingestion onward; preserve leading zeros and alphanumeric content |
| `status` | Observed condition; apply the approved readiness normalization, retaining PMCM/PMCS separately |
| `command` | Current command attribution supplied through the approved view relationship |
| `hrs_to_insp` | Numeric remaining inspection hours; source units/nulls and feature defaults must be verified |
| `hrs_to_phase` | Numeric remaining phase hours; do not infer utilization or reset rules from this field alone |
| `location` | Legacy-compatible context if supplied/required; not a readiness denominator or organization substitute |
| `reason` | Available maintenance/supply explanation; preserve text meaning; optional for readiness, used by NMCS grouping |

Core readiness requires date/tail/status and command for command reporting.
Enhanced1 requires the seven fields identified in STREAMLIT_PARITY; location and
reason are not trainer features. Missing prediction fields must not be fabricated
from simulator episode/action tables. Input validation and defaults must follow
the approved consumer contract; failures must not produce plausible substitute data.

The approved existing view's `COALESCE` behavior for inspection and phase hours
must be preserved, including its expression precedence and defaults. Do not
introduce alternative null handling in the adapter/application or modify the SQL
view. Exact restricted expressions/default values are not reproduced here and
were not independently verified; their preservation is a customer-approved
requirement. Prediction preprocessing remains a distinct compatibility check and
must not replace the view's established hours semantics.

## Internal organization projection

Parent Force -> Command Unit -> Battalion -> Tail is the authoritative mapping.
Use verified current relationships, not platform-derived or guessed associations.
Record extraction/assignment context internally so historical reports can be
understood as current-assignment attribution. Do not claim time-varying historical
ownership, backfill invented transfers or infer historically known ML command
features from current assignments.

Battalion mapping remains server-side and internal, even on the intranet. Ordinary
response models must explicitly allowlist fields and omit battalion names, keys
and relationship paths. Public payloads must contain no real organization metadata,
including opaque identifiers that can be mapped back to internal units. If mapping
is absent/ambiguous, report a controlled validation issue rather than inventing it.
The approved view might not project every hierarchy field; any supplemental mapping
source requires explicit approval. Do not alter the view to satisfy an assumption.

## Provider and API requirements

The production adapter must replace the manual extraction/BCP/CSV transport while
preserving the same observation population and reconstruction semantics. Keep the
business interpretation in the shared backend, never duplicate formulas in React.
Future SQL implementation must use approved read-only SELECT access, authored
allowlisted identifiers, parameterized values, connection/query timeouts, bounded
retrieval, complete coverage checks and deterministic resource cleanup. A bound
must reject incomplete data, not return readiness from truncated history.
Credentials must come through an approved local secret mechanism; never serialize
or log secrets, raw driver errors or internal connection details. Failure in SQL
mode must report the configured source and a safe error, never synthetic fallback.
Read-only client intent does not replace server-side least-privilege permissions.

Current FIS4 DataProvider has `source` and `load_events()`; SQL currently consumes
four event columns against a placeholder source contract. It is mocked, not wired
to the approved view. Its identifier constraints, duplicate conflict policy and
bounds require explicit source mapping review. Do not label that existing adapter
as completed intranet integration or assume its placeholder view must be created.

Current synthetic-history APIs use bounded immutable aggregates initialized once
per application lifecycle. Default CSV remains separate, and historical routes
are not exposed in CSV/SQL modes. Preserve existing contracts and failure isolation.
Do not transplant the simulator's fixed 160-tail/four-command population into
production. A production cache design needs approved refresh/cutoff/consistency
and per-worker memory acceptance; no arbitrary TTL or request-time regeneration
rule is established here. SQL snapshot consistency across an extraction must be
verified without changing historical data meaning.

Existing FIS4 historical window bounds differ from the legacy trend boundary;
record and approve an explicit compatibility strategy before any API change.
Platform filtering must use verified associations, the same snapshot/date context
and FIS-001 calculations. This document adds no route, response field or access claim.

## Public demonstration versus authorized intranet

| Boundary | Public demonstration | Authorized intranet |
|---|---|---|
| Observations and identifiers | Entirely fictional, non-identifiable | Approved read-only view |
| Organization/platform associations | Entirely fictional | Verified current associations |
| Battalion | No internal relationships or metadata exposed | Internal mapping only; absent from ordinary responses |
| Assets, bundles, APIs, errors, images and exports | No internal names, logos, categories or operational metadata | Explicit approved exposure/access policy |
| Prediction | Fictional inputs and approved sanitized artifacts only | Approved artifact lineage and inference compatibility |
| Access control | No authentication claim without implementation | Server-side authorization and least privilege required |

A trained artifact may contain real command categories or metadata even if no
training rows are exported. Do not bundle or publish it for public demonstration
without a separate artifact exposure review. Removing UI labels alone is insufficient.

## Prediction and runtime boundary

Use the selected Enhanced1 target/features exactly once their relationship to the
working Streamlit inference path is reconciled. Record artifact hash/provenance,
ordered features, missing-value policy, horizon, eligible statuses, positive class,
source/trainer version and approved package/native runtime versions in controlled
release evidence. Runtime compatibility is unverified: the existing artifact was
not opened, deserialized, scored, replaced or trained in this phase.

Do not assume the legacy environment matches the current FastAPI Python pins.
Scikit-learn, pandas, NumPy, joblib and Python compatibility require verified
versions and authorized dependencies before inference acceptance. Do not add them
as a side effect of this contract. Forecast output must not masquerade as current
readiness, calibrated probability, independent fault count or separate NMCS/NMCM
risk when the artifact provides only combined NMC estimates.

## FIS-002 deployment acceptance

Maintain one codebase and shared business logic for public demonstration and
intranet use. Cloud is configuration, not a fork of readiness/prediction logic.
The eventual Windows x64 offline ZIP must include compatible Python/dependencies,
native libraries, compiled React assets and verified artifacts; no destination
Node/npm/pip/internet/training or manual source edits. Preserve synthetic mode
for pre-connection verification and approved local secret configuration.

Deterministic start/stop/health/diagnostics/rollback, integrity manifests, dependency
inventory, security evidence and exact-package acceptance in a clean isolated
Windows x64 environment remain mandatory. SQL permissions, source contract,
TLS/certificate behavior, operational refresh and access-control dependencies need
separate acceptance; packaging cannot eliminate them. No packaging or deployment
was implemented or accepted by this documentation task.

## Integration acceptance sequence

1. Confirm sanitized physical-to-logical mappings, active criteria, current joins,
   timestamps/nulls and duplicate ordering without changing the view.
2. Freeze fictional parity fixtures against the approved working interpretation;
   cover daily reconstruction, filters, persistence, populations and FIS-001.
3. Reconcile Enhanced1 spelling/provenance, feature definitions, eligibility and
   artifact/runtime evidence; preserve unresolved discrepancies explicitly.
4. In a separately authorized task, implement/mock the provider projection and
   current organization/platform support with response exposure tests.
5. In separately authorized tasks, prove rule/inference parity and failure behavior,
   then perform restricted real SQL acceptance and FIS-002 offline acceptance.

Reject leaking battalion fields, operational public data, unauthorized SQL access,
truncated histories or silent SQL-to-synthetic fallback. Required tests include
fleet/command/platform reconciliation, leading-zero tails, missing days and
intra-day updates, current-assignment attribution, incomplete cache/source errors,
credential redaction, prediction window/censoring alignment, and ordinary response
field allowlists. No tests or application behavior are introduced here.
