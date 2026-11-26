-- Run in the operator-approved database. Catalog discovery only.
SET NOCOUNT ON;
SET LOCK_TIMEOUT 5000;

DECLARE @view_id int = OBJECT_ID(N'dbo.VW_MNT_AIRCRAFT_HISTORY', N'V');
IF @view_id IS NULL
    THROW 51000, 'View absent or metadata not visible. Ask the intranet operator.', 1;

SELECT c.column_id, c.name AS column_name, t.name AS declared_type,
       TYPE_NAME(c.system_type_id) AS system_type,
       c.max_length AS max_length_bytes, c.precision, c.scale,
       c.is_nullable, c.collation_name
FROM sys.columns AS c
JOIN sys.types AS t ON t.user_type_id = c.user_type_id
WHERE c.object_id = @view_id
ORDER BY c.column_id;

-- Run separately only with explicit definition-review permission.
-- A NULL definition can indicate restricted visibility or an encrypted view.
-- SELECT OBJECT_DEFINITION(@view_id) AS view_definition;
