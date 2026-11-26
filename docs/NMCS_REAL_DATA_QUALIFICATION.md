# NMCS real-data qualification contract

Proposed for architectural and intranet operator review. **All physical SQL
mappings and source assumptions are UNVERIFIED.** The qualification reference is
the logical `dbo.VW_MNT_AIRCRAFT_HISTORY` view. Its physical schema, name,
availability, filters, joins and semantics require attestation. This contract
authorizes neither database access nor training. Preserve the existing approved
view, FIS-001, FIS-002 and FIS-003.

## Required logical projection

| Logical field | Required qualification |
|---|---|
| Observation timestamp | Event time and source calendar, precision, correction and availability semantics; demonstrate what was visible at the reference cutoff |
| Aircraft key and tail | Stable longitudinal identity through tail renames, reuse and transfers; retain text and leading zeros; identifiers remain local |
| Status | Original code plus signed mapping; record ambiguous and unmapped counts |
| Command | Assignment effective and known at the reference time, with source and coverage; no backward attribution from current assignments |
| Platform | Independent aircraft attribute; verify stability or effective-dated changes, including when changes became available |
| Optional inspection/phase hours | Units, effective timestamp, availability, null/default provenance, nonnegative domain where applicable and established COALESCE semantics |
| Optional maintenance inputs | Reason, location or other approved predictors only when time-stamped, available as of reference and necessary; future repair, closure and receipt facts are excluded |

Use FMC, PMCM, PMCS, NMCS, NMCM and DEPOT as distinct canonical statuses.
PMC is the PMCM + PMCS reporting aggregate. A source value of PMC requires
a verified subtype mapping for six-state modeling; ambiguous PMC is quarantined,
never guessed. Unknown, blank and conflicting values are unavailable, not
negative. NMCS is Non-Mission Capable due to Supply and NMCM is Non-Mission
Capable due to Maintenance. The binary target is NMCS occupancy on exactly
T+H, H=1..180, from validated status on that date. A usable NMCM is negative.
Current NMCS remains eligible. This is neither onset nor any future NMC event.

## Temporal qualification and extraction

- Agree inclusive start and exclusive end in the approved source calendar.
  Extract adequate pre-reference lookback, outcomes only to the partition
  cutoff and no rows beyond the signed data watermark. Document timezone,
  working-day calendar, roster, refresh, late entry and correction behavior.
  If event timestamps alone cannot establish when values were available, require
  independent availability evidence or exclude the affected period or field.
- Order by stable aircraft identity and event time. Use a verified tie-breaker
  only if it represents the actual winning observation as of cutoff. Collapse
  identical equal-time rows, quarantine conflicting ties without a verified
  winner, and replay the established intraday latest/non-null behavior.
- Audit expected active working-day coverage using an approved roster and
  calendar independent of observation rows. Verify active/retired filtering
  and survivorship bias. No pre-entry backfill or carry past exit or the
  validated endpoint. A reference requires a fleet observation that day and
  a usable tail status. Label carry requires separately attested freshness,
  permitted gap lengths and calendar rules. Keep observed and validated carry
  separate, treat other gaps as unavailable, and audit missingness by subgroup
  and horizon. Unobserved starts/ends are left/right censored, not completed
  episodes. No synthetic defaults on gaps.
- The existing view is described as using current assignments. Qualify
  historical command/platform features only when effective and recorded dates
  or independently frozen as-of snapshots prove them. Without such evidence,
  block transfer of the frozen command/platform-dependent comparator. Any
  context-free alternative requires separately approved protocol/model work.
  Keep battalion internal. Preserve established readiness attribution.
- Verify whether inspection/phase values existed at the reference cutoff.
  Preserve approved view COALESCE behavior, but distinguish its defaults from
  observed measurements with approved evidence. Do not reverse-engineer
  missing hours from later rows or treat a default zero as measured zero.
  Mark unsupported optional inputs unavailable; fail if required by the
  frozen artifact. Phase 05B fitting dropped both all-missing hour inputs.

Use an operator-approved offline Windows x64 profiling client with the
approved SQL Server 2019 connection mechanism, TLS and certificates, and
least-privilege SELECT-only access to the designated view. Parameterize values,
fix and allowlist identifiers, use an approved consistent snapshot or signed
extraction watermark, set connection/query timeouts and row/date budgets, and
use bounded batches that neither drop nor repeat boundary rows. Abort on
truncation or inconsistent snapshots. Keep credentials in the approved local
secret mechanism. Keep raw extracts, profiling outputs, hashes, diagnostics
and access logs on authorized intranet storage. Git gets sanitized contracts
only. No live SQL was executed for this document.

## Sanitized SQL Server profiling templates

These templates use logical aliases and are **not physical queries**. For
each statement, prepend a `WITH scoped AS (...)` containing only the approved
column projection from the logical view. Bind typed `@from` and `@until` and
filter the verified physical observation column with `>= @from AND < @until`
inside that projection. Do not use SELECT star. The null timestamp profile
below needs a separately approved bounded population query because a date
predicate excludes null timestamps. Run aggregates locally and suppress
small cells before any approved summary sharing.

```sql
-- Row and tail counts, date bounds, and required-field nulls.
SELECT COUNT_BIG(*) AS row_count, COUNT(DISTINCT aircraft_key) AS tail_count,
       MIN(observation_ts) AS first_seen, MAX(observation_ts) AS last_seen,
       COUNT_BIG(*) - COUNT_BIG(aircraft_key) AS null_aircraft,
       COUNT_BIG(*) - COUNT_BIG(raw_status) AS null_status,
       COUNT_BIG(*) - COUNT_BIG(command_at_observation) AS null_command,
       COUNT_BIG(*) - COUNT_BIG(platform_at_observation) AS null_platform,
       COUNT_BIG(*) - COUNT_BIG(inspection_hours) AS null_inspection,
       COUNT_BIG(*) - COUNT_BIG(phase_hours) AS null_phase
FROM scoped;

-- In a separately bounded audit projection without the timestamp predicate.
SELECT COUNT_BIG(*) - COUNT_BIG(observation_ts) AS null_timestamp FROM scoped;

-- Equal-time duplicate count, with no identifiers returned.
SELECT COUNT_BIG(*) AS duplicate_groups, SUM(n - 1) AS extra_rows
FROM (
    SELECT COUNT_BIG(*) AS n FROM scoped
    GROUP BY aircraft_key, observation_ts HAVING COUNT_BIG(*) > 1
) AS duplicate_keys;

-- Raw status distribution. Audit mapping before encoding labels.
SELECT raw_status, COUNT_BIG(*) AS n FROM scoped GROUP BY raw_status;

-- Observed date coverage using the verified source calendar conversion.
SELECT observation_date, COUNT_BIG(*) AS observations,
       COUNT(DISTINCT aircraft_key) AS observed_aircraft
FROM scoped GROUP BY observation_date ORDER BY observation_date;

-- Completeness versus approved expected active tail/working-day pairs.
-- expected is an operator-approved roster/calendar CTE, not an assumed table.
SELECT e.calendar_date, COUNT_BIG(*) AS expected_pairs,
       COUNT_BIG(o.seen) AS observed_pairs,
       COUNT_BIG(*) - COUNT_BIG(o.seen) AS missing_pairs
FROM expected AS e
LEFT JOIN (
    SELECT DISTINCT aircraft_key, observation_date, 1 AS seen FROM scoped
) AS o ON o.aircraft_key = e.aircraft_key AND o.observation_date = e.calendar_date
GROUP BY e.calendar_date ORDER BY e.calendar_date;
```

Also profile conflicts over the full projected values for each duplicate key,
blank strings, unmapped codes, tail reuse, freshness gaps, availability-time
lag and roster reconciliation. Do not infer expected population from the
observed counts alone.

## Acceptance and independent validation

1. Require signed source/view lineage, mappings, extraction/security plan and
   as-of semantics. Included rows must have zero ambiguous identities,
   unresolved equal-time conflicts, unknown statuses or unverified mandatory
   field provenance. Reconcile raw/excluded/usable counts and active coverage.
   Quarantine exceptions with reasons and quantify selection bias. Block if
   partitions, rosters, carry eligibility or availability cannot be validated.
2. Lock coverage and freshness tolerances with the operator before inspecting
   outcomes. Report observed/carry/unavailable rates by period, horizon,
   command and platform. Require representative multi-year history and enough
   independent time blocks and class support after purging. Prove reconstruction
   on sanitized fixtures and local aggregate reconciliation. Unsupported
   subgroups or horizons cannot be accepted.
3. Pre-register independently reviewed chronological development, calibration
   if authorized, and sealed out-of-time periods with exact dates, eligible
   cohorts, horizons, outcomes, purge and source cutoffs. Freeze features and
   artifacts before any holdout access. Compare on identical rows against
   approved empirical baselines using proper scores, reliability, ranking,
   fleet-count errors, subgroup guards and paired aircraft/time-block intervals.
   Set operational margins and multiplicity before access. Require adequate
   independent support and reliability, no material harm, and reproducible
   evidence with exclusions, provenance and a one-time execution record.
4. Obtain operator/customer review of risks, intended decisions, monitoring
   and rollback. FIS-002 exact-package/offline and runtime gates remain
   separate. Fictional evidence cannot grant real-data prediction approval.

Blocking questions for the operator: What physical view and approved column
mappings exist? Can the source prove active roster membership, availability
time, winning corrections, historical assignments and stable aircraft identity?
What is the working-day calendar and maximum approved carry? Which hour
values were genuinely available and which are COALESCE defaults? How much
representative, independently held-out data remains after all gates?
