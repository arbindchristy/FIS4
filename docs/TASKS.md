# FIS4 task backlog

## Render Free-only focused preflight - 2026-11-23

Current publication status: [PR #14](https://github.com/arbindchristy/FIS4/pull/14)
is open on `feature/render-free-demo`; chief-architect source review approves the
deployment implementation. It is **not merged or deployed**. The approved approach
is Render Free at USD 0/month with Git-backed Docker; no paid compute or external
registry publication is required or authorized. Public-exposure approval, zero-charge
billing guards and actual Render build/startup/idle-wake acceptance remain open.
The verification and no-publication statements below describe their historical
preflight execution points, not the current PR status.

Customer decision: Render Free USD 0/month only; supersedes the earlier paid-candidate
recommendation below. Existing image reused; one 0.1 CPU/512 MiB startup, no rebuild.
Probe exit 0: readiness 557.6507 s; peak 263.42 MiB, warm 212.44 MiB; zero OOM.
20 sequential API, four concurrent requests and five subsequent health checks pass.
Focused portable deployment-test TypeScript exit 0; two browser cases pass in 6.3 s.
Original Docker/runtime/lock/POC spec unchanged; no application or dependency changes.
CONDITIONAL GO for pre-warmed fictional demo only. Actual Render build/idle wake,
unauthenticated public exposure approval and USD 0 billing guards remain open.
Git-backed Docker needs no external registry; exact ten-file PR allowlist, commands,
limits, security dispositions, smoke/rollback steps: deploy/demo/PREFLIGHT_REPORT.md.
No stage/commit/push/PR/deployment/account or billing operation performed.
Final security exit 0: 71 tracked/index files, zero violations; ten existing benign
leads dispositioned in report. Eight untracked files: zero extra leads. Whitespace,
protected scope, empty index and five original deployment file hashes PASS.


| Item | Status | Evidence or next action |
|---|---|---|
| Synthetic Docker/Render preflight | Implementation approved; PR #14 open, not merged or deployed | Render Free USD 0/month, Git-backed Docker; portable tests complete; recorded measurements unchanged; public-exposure approval, zero-charge guards, CVE and actual Render acceptance pending; see deploy/demo/PREFLIGHT_REPORT.md |
| P0 command-filter correction | Corrected; acceptance passed; chief-architect source review pending | Selected snapshot authoritative; old behavior fails three new cases; 136 regression, eight final scope, 47 browser passes/four skips plus three final demos; TypeScript/build/security pass; evidence/matrix in PROJECT_STATE |
| Command-centric readiness | Implemented; local verification passed; chief-architect review pending | One summary/command with nested platforms; 128 unit tests, six final command tests, TypeScript/build pass; browser 44 pass/four intentional skips; security zero violations/10 benign leads; no publication |
| Phase 03C-1B.2 frontend verification | Local gates passed; chief-architect review pending | 122/122 unit tests; TypeScript/build exit 0; full browser 41 passed/four intentional skips; strengthened follow-up six passed; actual mobile touch in both themes; security dispositions in PROJECT_STATE; no publication |
| Phase 03C-1B.1 React platform intelligence | Implementation written; source review pending | Separate platform section and validated clients, shared charts/windows, product identity; focused TypeScript exit 0; no suites/build run; Phase 03C-1B.2 must add/adapt tests and verify runtime behavior |
| Phase 03C-1A platform intelligence backend | Implemented; local verification passed; awaiting chief-architect review | Stable fictional metadata and additive cached APIs; 21 focused, 160 full, 155 portable tests and 12 harness checks pass; security exit 0, 0 violations, 10 existing leads dispositioned; unstaged/unpublished |
| PR #7 mobile chart touch scrolling | Fixed; local verification passed | One CSS value; actual touch regression fails before/pass after; 13 history browser passes (2 non-mobile skips), 61 component tests, TypeScript/build and 139 backend tests pass; recovered harness exit 0, 12/12 checks including 134 portable tests; physical devices deferred |
| Phase 01 readiness baseline | Complete | 28 passing tests; `TEST_REPORT.md` |
| Customer formula lock | Complete | `DECISIONS.md`, FIS-001 |
| Phase 01 GitHub publication | Complete | Baseline `a57936a8fff7e0502bceef008ea609fe4aef7379` |
| Phase 01.6 verification script | Complete; verified | Explicit and automatic selection each pass all 28 readiness tests |
| Phase 01.6 tracked-file security script | Complete; verified | 11 tracked files and isolated 17-file proposed scan: no violations or manual findings |
| Harness failure-path regression checks | Complete | `tests/test_engineering_harness.ps1`: 11 checks passed |
| State, backlog, release gates, end-of-task instructions | Complete | These documents, README, AGENTS; actual evidence in PROJECT_STATE |
| Phase 01.6 publication | Complete; stale status corrected | Local verified commit/refs: `bb3abfd036c2c7c88a03abf7e9cee628dd638f1c`; no live remote recheck |
| Phase 02A synthetic FastAPI | Implemented; acceptance checks passed | Health, fleet, command, distribution; 16 API tests; formulas unchanged |
| Dedicated environment and dependency pins | Complete | FIS4 `.venv`, CPython 3.13.7; 22 exact pins; pip check exit 0 |
| API harness and portable boundary | Complete | 44 full / 39 portable tests; original 28 tests and 11 harness scenarios preserved; 12 checks pass |
| Phase 02A staged review | Complete; checks passed | 11 reviewed files staged; 44 full / 39 portable tests, 12 harness checks, 22-file index/working-tree security scan; all exit 0 |
| Phase 02A publication | Published and merged per local history | Local HEAD d9d8ffa is merge of PR #1; prior reviewed commit ac4887e; no Phase 02B remote recheck |
| Phase 02B provider architecture | Implemented; mocked validation passed | Explicit synthetic/SQL providers, strict configuration, bounded SELECT, injection, safe errors and no fallback |
| Phase 02B regression suite | Verified | Original 44/39 retained; totals 79 full / 74 portable; 35 mocked-provider tests; 12 harness checks pass |
| Phase 02B native dependency | Installed after explicit approval; verified | pymssql==2.3.3; native import/signature and FreeTDS v1.4.26 checked; pip check passes; no native connection |
| Phase 02B security review | Complete; findings dispositioned | Proposed and post-staging 26-file scans exit 0; 0 violations; 6 source-expression leads, all resolved in PROJECT_STATE |
| Phase 02B localhost demonstration | Complete; user-reported success | Synthetic-data API on localhost; reported 2026-11-19; separate from mocked SQL and actual SQL Server testing |
| Phase 02B staged review | Complete; awaiting publication approval | 11 reviewed files staged; 79 full / 74 portable tests and 12 harness checks pass; protected baseline unchanged; post-staging security reviewed |
| Phase 02B publication | Published and merged per local history | c598ec4 contains Phase 02B PR #2; no fresh remote query during Phase 03A review |
| Real SQL Server 2019 integration | Deferred; separate authorization required | Schema/history mapping, credentials, permissions, TLS, actual driver/server timeout and load evidence unresolved |
| Production API / data integration | Deferred | Mocked SQL support does not authorize real data, database connectivity, SQL execution or ML |
| FIS-002 documentation | Committed separately; preserved | 8bd2ba87f52ed23574d6fb44e9cd5f74b4a219b4; AGENTS/DECISIONS unchanged in Phase 03A |
| Phase 03A React dashboard | Implemented; final review checks passed | API-owned metrics, filters, source labels, safe states; localhost synthetic mode only |
| Phase 03A frontend verification | Verified independently | TypeScript/build PASS; Vitest 32/32; Playwright 15/15 across desktop and two tablet viewports; live FastAPI synthetic integration PASS |
| Phase 03A dependency lock | Reviewed | 15 exact direct pins, lockfile v3 with 169 resolved entries/integrity records; installed versions match; no installs/upgrades during review |
| Phase 03A backend regression | Preserved and verified | 79 full / 74 portable tests, 12 harness checks; backend/engine/formulas unchanged |
| Phase 03A security and staging | Complete; final staged review passed | 23 reviewed files staged; 44-file proposed/post-staging scans exit 0, 0 violations; all 8 source-expression leads resolved in PROJECT_STATE; generated artifacts excluded |
| Phase 03A design references | Validation pending | No approved design reference found; new layout, no claimed visual match |
| Phase 03A publication | Merged, locally verified | main/starting HEAD 25b1eaa5e8e464247d9b49e38c468d0aa03b9dd3 contains PR #3; prior review records are historical |
| Phase 03B Task 1 fleet simulator | Merged via PR #4; locally verified | Baseline 37c8120f5d6c08a6650f94141a71faf156784d16; 160 fictional tails/four commands/four years; algorithm unchanged in API task |
| Phase 03B Task 1 verification | Passed | 98 full / 93 portable tests (original 79/74 preserved); 19 new tests; 12 harness checks; security findings dispositioned in PROJECT_STATE |
| Phase 03B-2A history provider/API | Implemented; local review | Explicit history mode, lifespan prepare-once cache, new history GET; old contracts/default/SQL paths preserved; docs/HISTORY_API.md |
| Phase 03B-2A tests/performance | Verified locally | 120 full / 115 portable tests; cold/warm/memory evidence in PROJECT_STATE; final harness/security dispositions recorded there |
| Phase 03B-2A publication | Merged through PR #5; locally verified | Current starting HEAD 9ac0f9aa7fc3243438363113ce920469344f3b8f; earlier pending status superseded |
| Phase 03B-2B Task 1 trend API | Implemented; local review | History-only GET series, bounded windows, six-status daily observations, strict validation, payload limit; no frontend changes |
| Phase 03B-2B Task 1 verification | Local evidence recorded | 139 full / 134 portable tests; 19 new tests; all-window response sizes/timings and harness/security outcomes in PROJECT_STATE |
| Phase 03B-2B Task 1 publication | Merged through PR #6; locally verified | Starting HEAD 726f34320c5ca658b70bd16b149b52dff3e724e5; prior pending status superseded |
| Phase 03B-2B Task 2 React history | Implemented; local review | Four windows, synchronized snapshot/trends, command counts, six-status composition, light/dark themes and keyboard/table access |
| Phase 03B-2B Task 2 verification | Passed | TypeScript/build; Vitest 61/61; Playwright 27/27 including real history backend; six actual theme screenshots; Python 139/134; harness 12/12; security dispositions in PROJECT_STATE |
| Phase 03B-2B Task 2 publication | Not authorized | Eighteen reviewed files remain unstaged and uncommitted; no push/merge/deploy |
| Rule-based / ML prediction | Not started | Future-only feature boundary documented; no targets, training, inference or prediction API |
| Offline deployment compatibility and packaging | Deferred | Destination-machine evidence and separate authorization required |

Do not convert missing dependencies, target-machine unknowns, or historical
legacy comments into approval to change FIS-001. Future work must reuse the
engineering checks and keep this backlog and `PROJECT_STATE.md` current.
