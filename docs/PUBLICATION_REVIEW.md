# Phase 01 publication preflight

Target: private GitHub repository `arbindchristy/FIS4`, branch `main`.
This review prepares a staged baseline; committing and pushing require explicit
user approval of the exact staged file list. No commit or push is represented
by this document.

## Verification actually performed

- Ran `C:\AI\Projects\fleet_cpi_suite\venv\Scripts\python.exe -B run_phase01.py`
  from `C:\AI\Projects\FIS4`: **28 tests passed**, zero failures, errors, or skips.
  The generated `TEST_REPORT.md` records actual output and environment versions.
- The test runner confirmed unchanged metadata for 18,034 legacy files and
  unchanged, hash-pinned source references during verification. It did not read
  operational data, credential/configuration contents, or model artifacts.
- Inspected the calculation module, both test files, runner, documentation,
  test report, and the entire synthetic fixture before staging. The approved
  formulas are unchanged, including NMCM in the serviceability denominator.
- Git version: `2.50.1.windows.1`. GitHub connector authentication identifies
  the repository owner and confirms private visibility and push permission.
- GitHub branch inspection returned no branches. Read-only Git CLI
  `git -c credential.interactive=never ls-remote --symref https://github.com/arbindchristy/FIS4.git`
  succeeded outside the network sandbox and returned no refs. No remote history
  was advertised at inspection time. A future push must remain non-forced and
  must recheck remote state before publication.

## Recorded SHA-256 baseline

| File | SHA-256 |
|---|---|
| `readiness.py` | `da787ff2b3e41fe2a1e89dd41d038323e7bfcfd1aea4e911e41efe33b1357eee` |
| `tests/test_readiness.py` | `d83905dd244841bea42f8f31e42ded64fb9a3861224b02be700f982b8bbd3db8` |
| `data/synthetic_readiness.csv` | `d24fac932ee57d563371a99a978787c476d179bd647e6c95a096866f0cc58c71` |

Module and test hashes match the previously recorded Phase 01 baseline. The
fixture hash records the unchanged, newly authored Phase 01 synthetic fixture.

## Security findings and disclosure

No embedded credentials, API keys, access tokens, private keys, private IP
addresses, internal database hostnames, or operational aircraft records were
found in the reviewed files. Checks combined pattern scans with source review;
they are not a guarantee against every possible secret format.

The fixture was authored during Phase 01 and has 11 fictional input events:
DEMO-X/DEMO-Y platforms, BASE-A/BASE-B locations, commands A/B, and dummy tail
identifiers 0001 through 0007 plus the deliberate invalid BAD row. Its origin
is the Phase 01 authored fixture, not a legacy operational-data export. No
legacy application files were copied into FIS4 for publication.

**Non-secret local-environment disclosure:** reviewed files retain the
user-supplied `C:\AI\Projects\FIS4` and legacy-reference paths, `C:\Python313`,
Python/package versions, and legacy source filenames/hashes for reproducibility.
These are intentionally identified for approval before publication. No Windows
username, machine name, database endpoint, authentication material, or personal
home-directory path was found in the proposed files. The comparison tests still
require the external, hash-pinned legacy source at the documented local path;
those source files are not included in the repository.

`.gitignore` excludes environments, caches, configuration/secrets, wheels,
builds/releases, models, logs, and datasets by default. Only the named fictional
CSV fixture is allowed through the data exclusions. Staging must use an explicit
file allowlist, followed by inspection of the complete staged diff and file list.

## Authorized publication boundary

After explicit user approval only, create the commit with message:

```text
FIS4 Phase 01: customer-approved readiness baseline
```

Push normally to `origin/main`; never force-push or replace existing history.
Verify the resulting GitHub ref and commit against the local commit and confirm
the committed file list contains no excluded artifacts. No FastAPI, React,
formula changes, test changes, dataset changes, or dependency installation are
part of this publication task.

## Local staging verification

Git was initialized only in FIS4 on main, with the requested origin. Existing
commit identity configuration is present; its personal details are not published.
The sandbox-created Git directory has different ownership from the desktop user,
so Git commands use a per-command safe.directory exception for FIS4 only. No
global trust setting was changed. The report was normalized from CRLF to LF
for Git whitespace checks; no report content or calculation/test/fixture bytes
were changed. Fifteen exclusion examples passed git check-ignore, while every
reviewed publication file remained allowed.
