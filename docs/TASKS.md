# FIS4 task backlog

| Item | Status | Evidence or next action |
|---|---|---|
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
| Phase 02A publication | Pending explicit approval | Staging authorized; no commit, push or external network operation performed |
| Production API / data integration | Deferred; separate instruction required | Synthetic local acceptance does not authorize real data, SQL or ML |
| React phase | Not started; separate instruction required | No UI work in Phase 01.6 |
| Offline deployment compatibility and packaging | Deferred | Destination-machine evidence and separate authorization required |

Do not convert missing dependencies, target-machine unknowns, or historical
legacy comments into approval to change FIS-001. Future work must reuse the
engineering checks and keep this backlog and `PROJECT_STATE.md` current.
