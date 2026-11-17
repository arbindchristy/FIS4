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
| Phase 01.6 commit | Awaiting explicit user approval after verification | No staging/commit/push automatically |
| API phase | Not started; separate instruction required | No FastAPI work in Phase 01.6 |
| React phase | Not started; separate instruction required | No UI work in Phase 01.6 |
| Offline deployment compatibility and packaging | Deferred | Destination-machine evidence and separate authorization required |

Do not convert missing dependencies, target-machine unknowns, or historical
legacy comments into approval to change FIS-001. Future work must reuse the
engineering checks and keep this backlog and `PROJECT_STATE.md` current.
