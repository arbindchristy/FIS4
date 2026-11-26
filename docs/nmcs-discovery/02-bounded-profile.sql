-- BLOCKED until the operator approves all mappings and the execution plan.
-- Edit a local copy. Replace three bracketed column placeholders and set the
-- typed parameters to approved bounds. Adapt the parameter type to match the
-- physical timestamp and convert to the approved source calendar for day bins.
SET NOCOUNT ON;
SET LOCK_TIMEOUT 5000;

DECLARE @from datetime2(7) = NULL, @until datetime2(7) = NULL;
IF @from IS NULL OR @until IS NULL OR @until <= @from
   OR @until > DATEADD(day, 31, @from)
    THROW 51001, 'Set an approved half-open window of at most 31 days.', 1;

;WITH bounded AS (
    SELECT TOP (100001)
           [APPROVED_TIMESTAMP_COLUMN] AS observation_ts,
           [APPROVED_AIRCRAFT_KEY_COLUMN] AS aircraft_key,
           [APPROVED_STATUS_COLUMN] AS raw_status
    FROM dbo.VW_MNT_AIRCRAFT_HISTORY
    WHERE [APPROVED_TIMESTAMP_COLUMN] >= @from
      AND [APPROVED_TIMESTAMP_COLUMN] < @until
), scoped AS (
    SELECT observation_ts, aircraft_key, raw_status,
           CONVERT(date, observation_ts) AS observation_day
    FROM bounded
), grouped AS (
    SELECT observation_day, raw_status,
           GROUPING_ID(observation_day, raw_status, aircraft_key, observation_ts) AS kind,
           COUNT_BIG(*) AS n, COUNT_BIG(DISTINCT aircraft_key) AS aircraft_count,
           COUNT_BIG(*) - COUNT_BIG(aircraft_key) AS null_keys,
           COUNT_BIG(*) - COUNT_BIG(raw_status) AS null_statuses
    FROM scoped
    GROUP BY GROUPING SETS ((), (observation_day), (raw_status),
                           (aircraft_key, observation_ts))
), sized AS (
    SELECT *, MAX(CASE WHEN kind = 15 THEN n END) OVER () AS total_rows
    FROM grouped
)
SELECT 'WINDOW' AS metric, CAST(NULL AS date) AS day,
       CAST(NULL AS nvarchar(4000)) AS status_code,
       n AS rows_or_groups, aircraft_count, null_keys, null_statuses,
       CAST(NULL AS bigint) AS extra_rows
FROM sized WHERE kind = 15 AND total_rows <= 100000
UNION ALL
SELECT 'DAY', observation_day, NULL, n, aircraft_count, NULL, NULL, NULL
FROM sized WHERE kind = 7 AND total_rows <= 100000
UNION ALL
SELECT 'STATUS', NULL, CONVERT(nvarchar(4000), raw_status), n, aircraft_count,
       NULL, NULL, NULL
FROM sized WHERE kind = 11 AND total_rows <= 100000
UNION ALL
SELECT 'DUPLICATE_KEY', NULL, NULL, COUNT_BIG(*), NULL, NULL, NULL,
       COALESCE(SUM(n - 1), 0)
FROM sized WHERE kind = 12 AND total_rows <= 100000 AND null_keys = 0 AND n > 1
HAVING EXISTS (SELECT 1 FROM sized WHERE kind = 15 AND total_rows <= 100000)
UNION ALL
SELECT 'ROW_CAP_EXCEEDED', NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM sized WHERE kind = 15 AND total_rows > 100000;
