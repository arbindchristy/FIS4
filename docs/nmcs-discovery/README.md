# NMCS historical discovery package

Use the [qualification contract](https://github.com/arbindchristy/FIS4/blob/cbc816665b7653ee292886f8c05036de477e385d/docs/NMCS_REAL_DATA_QUALIFICATION.md). The
contract is referenced at its reviewed revision because it is pending in
the separate Phase 05B draft. The logical view is dbo.VW_MNT_AIRCRAFT_HISTORY. Physical mappings and source
assumptions remain UNVERIFIED. Run only inside the authorized Windows intranet.

The existing provider in api/providers.py uses pinned pymssql 2.3.3, literal
allowlisted SELECT statements, bound values and timeouts. It serves readiness
through a different projection. Use the operator's already approved SQL client
instead of repurposing that provider or installing packages.

## Run order on Windows

Prerequisites: operator approval of the connection, target database and work
window; an existing approved SSMS or sqlcmd installation; approved
authentication and TLS certificate validation; metadata visibility for Step 1,
SELECT on the approved view for Step 2, and separate permission to read its
definition (object-level VIEW DEFINITION or approved equivalent). Verify the
selected database in the client before execution. Use a dedicated session with
implicit transactions off and no open transaction. These scripts do not start
a transaction or change isolation. Avoid NOLOCK and use the operator-approved
consistent snapshot or immutable watermark. SQL lock timeout limits lock waits;
the client timeout separately limits execution.

1. Copy these sanitized files to an approved local intranet folder. In SSMS,
   connect using the approved authentication option, select the approved
   database, and open 01-view-metadata.sql. Set an execution timeout of 30
   seconds (or a stricter local limit). Execute the catalog batch. For approved
   definition review, run the batch with its last SELECT uncommented. Keep the
   definition and physical metadata inside the intranet. If metadata is absent,
   stop and have the operator distinguish permissions from an incorrect mapping.
2. Obtain signed mappings for timestamp/date calendar, stable aircraft key and
   status. Review the local copy of 02-bounded-profile.sql with the operator.
   Replace only the marked identifier placeholders and set the typed dates.
   Start with one approved day. Execute only after the operator checks a
   date-restricted access plan with bounded reads within the approved resource
   budget. A TOP row guard does not cap storage reads; if a scan or plan cannot
   be bounded, block execution. CTEs may be re-evaluated for multiple output
   branches, so review the total plan, including sorts, memory and tempdb use.
   Verify the mapped types support grouping and preserve key/status distinctions.
3. Treat ROW_CAP_EXCEEDED, timeout, or incomplete output as BLOCK. Do not use a
   partial population. Narrow the window with approval. Adjacent windows use
   nonoverlapping half-open boundaries; distinct aircraft counts across windows
   cannot be summed. The date-filtered scope cannot count null timestamps, and
   repeated keys are not proof of conflicting observations. No baseline or
   operational prediction approval follows from passing these checks.

For an already approved sqlcmd client **with Windows integrated authentication**
and requisite TLS options, run from PowerShell in the local package directory:

```powershell
sqlcmd.exe -S '<approved-server>' -d '<approved-database>' -E -N -l 5 -t 30 -b -i '.\01-view-metadata.sql'
# Only after approved local mapping, bounds and plan review:
sqlcmd.exe -S '<approved-server>' -d '<approved-database>' -E -N -l 5 -t 30 -b -i '.\02-bounded-profile.sql'
```

Replace the two connection placeholders locally. Confirm the installed client's
approved encryption syntax and expected certificate validation before using the
commands. Never bypass certificate validation or put passwords on command lines.
If integrated authentication is not approved, use the existing authorized SSMS
connection workflow. A nonzero sqlcmd exit is BLOCK; the row-cap result also
requires manual disposition. Do not redirect to shared storage.

Use RESULTS_TEMPLATE.md for a sanitized review. Raw client output, code values,
exact operational counts/dates, physical names, definitions and aircraft
identifiers stay inside the intranet. Share only approved coarsened aggregates
with small-cell suppression. These SQL files have not been run on SQL Server.
