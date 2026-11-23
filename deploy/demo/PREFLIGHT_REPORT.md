# FIS4 customer-demo Docker/Render preflight

Updated 2026-11-23. Recommendation: **CONDITIONAL GO for a pre-warmed Render Free
synthetic demonstration at USD 0/month. Technical local Free-profile gate PASS;
public access and actual Render acceptance remain approval gates.** This is not production, SQL, ML or
FIS-002 Windows offline-package acceptance.

## Baseline and scope

- Existing detached worktree: `C:/AI/Projects/FIS4/.harness-test-tmp/demo-preflight`.
- HEAD: `8ad8f9173429672b04957d3ee381851422dc5eae`, merged main PR #13.
- GitHub `refs/heads/main` was checked read-only and matches this exact commit.
  No reconciliation is required. Command-filter correction is present.
- Main working tree remains on `fix/command-filter-scope`, HEAD
  `9e408e8220a11eb00e8fa3b6945a6264bcaa21d3`; its tracked tree matches merged main.
  Three pre-existing untracked patches/launcher are untouched.
- No image rebuilt, dependency installed, pin changed, service stopped/restarted,
  worktree deleted, source overwritten, branch created, staging or publication
  performed in this completion task. The existing localhost container is preserved.
- No readiness, React, simulator, provider, SQL, prediction or protected decision
  changes. Only deployment documentation and two portable deployment-test files are added
  or updated in this follow-up. Existing deployment files remain byte-for-byte unchanged.

## Exact inventory and minimal diff

Existing, previously untracked POC files preserved:
1. `.dockerignore` (default-deny build context)
2. `deploy/demo/Dockerfile` (two stages; pinned image digests)
3. `deploy/demo/server.py` (synthetic-only composition/static serving)
4. `deploy/demo/requirements-linux.lock` (19 exact existing pins with wheel hashes)
5. `deploy/demo/acceptance.spec.ts` (two existing container surface tests)

Completion documentation:
6. `deploy/demo/PREFLIGHT_REPORT.md` (this report)
7. `docs/PROJECT_STATE.md` (new preflight evidence section only)
8. `docs/TASKS.md` (new preflight row only)
9. `docs/RELEASE_GATES.md` (new conditional demo gate only)

Free follow-up adds two portable test files (listed in the final ten-file PR
allowlist below); the original machine-specific spec is excluded from that PR.

Raw evidence is outside the proposed PR/build context at
`C:/AI/Projects/FIS4/.harness-test-tmp/demo-evidence/`. Existing logs/images remain;
new focused evidence uses `completion-browser.txt`, `completion-browser-results/`
and `completion-runtime.json` without replacing earlier evidence.

## Image and runtime identity

Existing tag: `fis4-demo-preflight:8ad8f91`.
Local image ID: `sha256:838b457e15cb061a9e9748df6358bb7bec3c878511397719089ea8e8a6d123c5`.
Reported image size: 406,785,897 bytes. No registry publication has been performed or is needed: the proposed Render
service builds from the reviewed Git commit using the existing Dockerfile.

The Dockerfile pins Node 24.4.1/bookworm-slim and Python 3.13.7/slim-bookworm by
Linux amd64 manifest digest. Build log confirms npm 11.4.2, Node 24.4.1, TypeScript,
Vite production build (282 ms) and pip check with no broken requirements. Python
runtime imports previously verified NumPy 2.3.4, pandas 2.3.3 and pydantic_core
2.50.4. No Node runtime or pymssql package is present in the final image.
Canonical Windows requirements/package-lock remain unchanged.

### Python dependency compatibility

Official exact-version PyPI metadata and candidate wheel hashes are retained in
`python-compatibility.json`. The runtime installation used wheels only, exact pins
and --require-hashes. Pure-Python wheel presence alone is metadata evidence; actual
successful runtime closure is established by the existing Docker build/pip check.

| Canonical dependency | Linux Python 3.13 x64 evidence | Image |
|---|---|---|
| annotated-doc==0.0.7 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| annotated-types==0.8.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| anyio==4.16.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| certifi==2026.10.23 | Compatible wheel metadata; Python requirement permits 3.13 | Excluded: HTTP contract-test closure |
| click==8.5.1 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| fastapi==0.164.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| h11==0.16.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| httpcore==1.0.9 | Compatible wheel metadata; Python requirement permits 3.13 | Excluded: HTTP contract-test closure |
| httpx==0.28.1 | Compatible wheel metadata; Python requirement permits 3.13 | Excluded: HTTP contract-test closure |
| idna==3.20 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| numpy==2.3.4 | Compatible wheel; native import verified | Installed, exact pin |
| opentelemetry-api==1.45.2 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| pandas==2.3.3 | Compatible wheel; native import verified | Installed, exact pin |
| pydantic==2.14.3 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| pydantic_core==2.50.4 | Compatible wheel; native import verified | Installed, exact pin |
| pymssql==2.3.3 | No CPython 3.13 manylinux x64 wheel; Windows/macOS wheels exist | Excluded: SQL-only |
| python-dateutil==4.0.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| pytz==2026.6 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| starlette==1.10.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| typing-inspection==0.4.5 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| typing_extensions==4.16.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| tzdata==2026.6 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |
| uvicorn==0.54.0 | Compatible wheel metadata; Python requirement permits 3.13 | Installed, exact pin |

SQL omission is deliberate and isolated: connect_pymssql imports the driver lazily;
server.py creates synthetic_history with no SQL settings/credentials and exposes
no provider-selection endpoint. No source build, driver replacement or pin upgrade
was attempted. This says nothing about Linux SQL integration compatibility.

### Local constrained measurements (not Render measurements)

| Check | Actual result | Evidence |
|---|---|---|
| Initial 1 CPU / 2 GiB lifespan readiness | 33.43 s; health synthetic/ok | runtime.json |
| Initial container-accounted peak | 263.77 MiB | runtime.json |
| Clean stop | 1.04 s, exit 0, shutdown complete | restart.json / restart-probe.txt |
| Restart, 0.5 CPU / 512 MiB | 94.12 s; no OOM | restart.json |
| Constrained startup peak | 276.64 MiB cgroup; process RSS HWM about 299 MiB | restart.json |
| Constrained warm memory | 217.77 MiB cgroup | restart.json |
| Warm series HTTP cases | 12 pass: All/A/B times 30/90/180/365; max 39.82 ms | restart.json |
| After completion browser checks | current 228,315,136 bytes; peak 290,078,720 bytes | completion-runtime.json |
| Existing processes | one `python -B demo_server.py` | docker top, current inspection |

Cgroup-accounted memory differs from process RSS/shared pages. Peak includes probe
process overhead and native allocations; do not substitute earlier tracemalloc
numbers. Local fractional CPU, OS cache, hardware and networking differ from Render.
These measurements support a small demo, not a concurrency/load SLA.

Existing run configuration: non-root UID/GID 10001, read-only root, tmpfs /tmp
64 MiB, capabilities dropped, no-new-privileges, PID limit 64. Container port 10000
is published only to 127.0.0.1:18080. One Uvicorn worker; OPENBLAS_NUM_THREADS=1 and
OMP_NUM_THREADS=1. Render steps must preserve thread limits and single instance.
Local Docker hardening flags are not claimed to be configurable identically on
Render; managed-runtime controls require provider acceptance.

## Functional and exposure evidence

Previous run `browser.txt`: 32 application browser passes, four intentional
non-mobile touch skips, one new static-route pass and one new exposure-test failure.
The latter expected 422 for a syntactically valid unknown command; existing fleet
contract correctly returns 404. The test was corrected, with a separate malformed
command 422 assertion. `browser-container-final.txt`: both new container tests pass.
This is combined evidence, not a claim of a clean full rerun. No application API
contract was changed to satisfy the test.

Completion run: nine/nine pass, no skips/retries, 24.5 seconds, against the retained
0.5 CPU / 512 MiB container. Selected only all-window/date alignment, actual HTTP
All -> A -> B -> All, and independent nested platform reconciliation for desktop,
tablet and mobile. Passing earlier touch/theme/fault-injection suites were not rerun.

Exact completion command, from the existing main checkout's frontend directory:

```powershell
npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run test:e2e -- --config=../.harness-test-tmp/demo-evidence/playwright-container.config.mts --project=history-desktop --project=history-tablet --project=history-mobile --grep 'acceptance demonstration|all windows and command/date|each command appears once' --output=../.harness-test-tmp/demo-evidence/completion-browser-results
```

| Requirement | Evidence | Status/limit |
|---|---|---|
| Compiled React and direct refresh | Existing container surface tests at / and /dashboard | Pass; other arbitrary frontend paths intentionally 404; no URL-persisted filters implemented |
| Fleet/A/B/restored All | Actual browser request/response evidence, three viewports | 94.6/88.1/160 -> 92.3/90.0/40 -> 94.4/85.0/40 -> fleet; serviceability/availability/tails |
| All six statuses | Browser compares every status count with actual HTTP distribution | Pass, PMCM/PMCS distinct |
| Nested platforms | Every command once, separate owner selectors/figures, all partitions sum to fleet | Pass, no battalion fields |
| Dates and all windows | Command C/date 2024-11-20 plus 30/90/180/365 controls | Pass, reset returns latest fleet |
| Stale-response/source/errors | Earlier real-browser delayed/cancelled requests and injected HTTP faults | Pass; SQL response simulation is not SQL access |
| Startup readiness | Lifespan awaits cache initialization before Uvicorn accepts requests | Pass locally; /health returns 200 synthetic/ok only after readiness |
| Unsafe paths/methods | .env/source files/docs/OpenAPI/unknown assets 404; POST readiness 405 | Pass |
| External frontend requests | Root/dashboard reload test tracks origin | None observed; no runtime CDN |

## Data/artifact security disposition

The recorded final-image inventory contains exactly 14 application/static files:
11 Python application/launcher files plus compiled HTML/JS/CSS. All 11 source hashes
match this worktree; current served HTML/JS/CSS hashes match the recorded image.
No models, training data, original Streamlit/SQL definitions, .git, environment files,
credentials, real organization mappings, data exports or source maps are copied.
Generated tails are deterministic fictional 000001..000160, with fictional commands;
ordinary APIs return aggregates, not tail/battalion records. No SQL or ML execution.

Artifact regex checks found zero leads, and included Python/OS inventories are
retained in evidence. This is data-exposure/static review, not a vulnerability/CVE
attestation or proof of authentication. Generic SQL-provider/configuration class
source remains in the shared application, including sanitized placeholder SQL;
it has no operational settings, usable driver, secrets or public selector in this
image. This preserves one business codebase rather than implementing a cloud fork.
Autogenerated docs/Redoc/OpenAPI are disabled in this composition to avoid CDN
requests/introspection; all existing business /api and /health contracts remain.

Completion security command: `scripts/security_check.ps1` from the deployment
worktree, exit 0; 71 tracked/index files, zero confirmed violations and 10 existing
manual leads (five expressions in both index and working tree). All dispositioned:
api/config.py:30 is a SecretStr declaration, api/providers.py:86 is runtime settings
binding, api/providers.py:89 is injected-secret binding, dashboard.spec.ts:14 is a
loopback hostname comparison, and historical PROJECT_STATE server-reuse text is a
scanner suffix match. None contains a live credential or operational endpoint.
The scanner's REVIEW REQUIRED status is retained; these are reviewed benign leads.
All six untracked POC/report files were explicitly scanned with the unchanged
Inspect-Text rules: zero additional leads. No links/binary/oversized files found.
Tracked Git whitespace and protected-file checks pass; all five pre-existing POC
file hashes are preserved. No index changes. No broad Python/frontend regression,
engineering-harness rerun, image rebuild or repeat startup measurement was needed:
no production source/pins changed, and the missing constrained-browser evidence is
now complete. These static checks are not a CVE scan or security certification.

## Render assessment and approval decisions

Reviewed official documentation on 2026-11-23:
- https://render.com/docs/compute-plans
- https://render.com/hosting/docker
- https://render.com/docs/free
- https://render.com/docs/inbound-ip-rules
- https://render.com/docs/private-services
- https://render.com/docs/health-checks
- https://render.com/docs/build-pipeline
- https://render.com/docs/deploying-an-image
- https://render.com/docs/rollbacks

### Free-only decision and focused test

The customer selected Free only, USD 0/month. Starter and all paid services are
excluded. This supersedes the prior paid-candidate recommendation; it does not
authorize a Render connection, publication, billing or public access.

One additional container was started from the existing image, leaving the original
0.5 CPU container and all prior evidence intact. No image build was repeated.

```powershell
docker run -d --name fis4-demo-free-preflight-8ad8f91 --memory=512m --memory-swap=512m --cpus=.1 --pids-limit=64 --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --cap-drop=ALL --security-opt=no-new-privileges -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 -p127.0.0.1:18081:10000 fis4-demo-preflight:8ad8f91
.venv/Scripts/python.exe -B .harness-test-tmp/demo-evidence/free_probe.py
```

The first command is executed once by the probe, not a separate second startup.
Evidence: free-probe.txt and free-runtime.json. Probe exit 0/PASS; CPU quota
10000/100000 and memory limit 536870912 bytes verified. Readiness: **557.6507 s**
(9m18s), versus the documented 900-second new-deploy health window; local margin
342.35 s. Startup peak **263.42 MiB** (276213760 bytes), warm **212.44 MiB**
(222756864 bytes); zero OOM/limit events. One worker, synthetic/ok health.

Twenty sequential HTTP checks pass: All/A/B snapshots and six-status distribution,
four series windows for each scope, and two command platform partitions. Maximum
sequential latency 809.6 ms. Four simultaneous requests (health plus three 365-day
series) pass, max 217.2 ms. Five subsequent health requests pass, max 91.4 ms.
First successful health response took 1.73 s, below the five-second health deadline.
This small local probe establishes feasibility, not capacity or a Render SLA.

Render Free is 0.1 CPU/512 MB and spins down after 15 minutes of inactivity. The
in-memory history is rebuilt on every cold start. Expect many minutes of waiting,
not the provider's generic approximately one-minute wake description. The 15-minute
health window is documented for new deployments; equivalent idle-resume grace is
not established here. Actual Render initialization, idle wake, memory and request
checks remain mandatory. No keepalive workaround is proposed. Pre-warm manually
before the appointment and confirm /health before sharing; cold-link availability
and production reliability are not accepted.

Free grants 750 instance hours per workspace/month and includes finite bandwidth
and build minutes. Exceeding bandwidth can incur charges with a payment method;
without one Free services suspend. Build-minute overage likewise requires explicit
budget controls. To uphold USD 0: Hobby workspace, Free compute, no paid add-ons,
no disk/database/registry/custom-domain purchase, no automatic upgrades; retain no
billable payment method and set any available build spend limit to zero. If the
account cannot guarantee zero-charge behavior, stop rather than accept a paid step.
No account/billing settings have been accessed or changed.

Git-backed Docker uses Render's own build infrastructure and image storage; no
external registry subscription or push is necessary. Build resources differ from
Free runtime resources. The prior successful local build is retained; the first
Render build is still unverified and will run only after deployment approval.

Access remains a separate gate: the app has no authentication. TLS, account login
and URL secrecy do not restrict customer access. Built-in web-service IP rules
require paid workspace features, which are excluded. At USD 0, either explicitly
approve unauthenticated fictional public exposure or keep sharing via localhost
screen-share. No authentication or protection is claimed or implemented.

## Exact proposed hosting procedure (future approval required)

1. Review the ten-file PR allowlist below and approve publication separately. Keep
   original services/evidence and the machine-specific POC test unchanged.
2. After approved commit/PR/merge, record the exact reviewed main SHA. Connect only
   that repository to Render after separate hosting and public-exposure approval.
3. New Web Service, Git repository, Language Docker; root context `.` and Dockerfile
   `deploy/demo/Dockerfile`. Choose **Free**, one instance and an approved region.
   Leave Docker command blank (existing CMD), no custom build/predeploy command,
   no disks, databases, secret files or registry credentials. Disable auto deploy.
4. Set PORT=10000, OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1; health path `/health`.
   Launcher fixes synthetic_history/as_of 2026-11-20/seed 42017; no SQL/provider/model
   overrides. Confirm the USD 0 guards above before creating the service.
5. Deploy only after explicit approval. Record Render build commit/artifact identity,
   logs, startup/memory and health response times. Require healthy within 15 minutes;
   on failure stop acceptance, do not upgrade or alter application functionality.
6. Execute the smoke checklist, then allow idle shutdown and measure one real wake
   before customer acceptance. Confirm no OOM, health under five seconds when warm,
   correct scope/source, and acceptable cold wait. Do not distribute a failed link.
7. Pre-warm for the scheduled demo, wait for healthy readiness, then share only with
   approved disclosure of fictional data, no authentication and Free limitations.

## Customer smoke-test checklist

- Verify approved access restrictions and HTTPS; unauthorised direct-origin access
  must be denied if a protected sharing model was chosen.
- /health: status ok/source synthetic. UI prominently SYNTHETIC with fictional-data
  and current authentication disclosure. No SQL or model connections/configuration.
- Default All Commands at 2026-11-20: serviceability 94.6%, availability 88.1%,
  160 tails; six counts FMC/PMCM/PMCS/NMCS/NMCM/DEPOT = 135/2/4/7/8/4.
- Select A and Apply: 92.3%, 90.0%, 40; counts 35/0/1/1/3/0. Only A summary appears.
- Select B and Apply: 94.4%, 85.0%, 40; counts 34/0/0/4/2/0. No A values/trend linger.
- Restore All: original fleet metrics/population; reset returns latest fleet/date.
- Expand two commands; select same platform independently. Compare each row/trend
  to command-scoped API, reconcile six counts and ensure no battalion fields.
- Test all four windows, valid historical date 2024-11-20, command filters, rapid
  window/platform changes, both themes, keyboard and mobile horizontal touch.
- Reload / and /dashboard directly. They reload the latest fleet snapshot; filter
  state is not URL-persisted. Unrecognised paths/API routes must not return HTML.
- /docs, /openapi.json, source/config paths remain 404; malformed input is safe
  422, syntactically valid unknown fleet command is 404, mutation is rejected.
- Inspect network values/parameters against displayed KPIs, all statuses and charts;
  there must be no external runtime asset request or silent fleet fallback.
- Record runtime memory and restart readiness on Render; local timing is not an SLA.

## Rollback and withdrawal (future approved hosting only)

- Before release, record known-good Git commit and retained Render deploy identity, service configuration,
  approved access controls, environment values and a retained Render deploy artifact.
- On incorrect scope, non-synthetic output, health failure or exposure: withhold the
  customer URL and block access at the approved entry control. Do not repair by
  switching data source or changing formulas.
- In Render Deploys, select the last known-good successful deploy, Rollback, then
  Rollback to this deploy. Confirm automatic deploys are disabled. Render reuses
  retained artifacts; Free retains only the two most recent previous deploys. This procedure is documented,
  not exercised against a hosting account.
- Recheck deploy/commit identity, approved access model, environment/thread/instance settings,
  /health and the All/A/B/All smoke sequence. Do not assume rollback covers every
  gateway/workspace setting. No persistent application disk/data migration exists.
- If no prior good deploy exists, suspend/withdraw the newly authorised service
  under the approved incident procedure; use localhost screen-share as fallback.
  Keep existing local services, worktrees and evidence; do not delete or reset them.

## Minimal PR plan and remaining blockers

Reuse four runtime/context files unchanged. The machine-specific
`deploy/demo/acceptance.spec.ts` stays local and is excluded from the PR.
Its two cases now have portable equivalents in `frontend/e2e/demo.spec.ts` with
`frontend/playwright.demo.config.ts`. The config targets an existing loopback image
only and never starts/stops servers. No new package or application behavior.

Exact ten-file PR allowlist:
- .dockerignore
- deploy/demo/Dockerfile
- deploy/demo/server.py
- deploy/demo/requirements-linux.lock
- deploy/demo/PREFLIGHT_REPORT.md
- frontend/e2e/demo.spec.ts
- frontend/playwright.demo.config.ts
- docs/PROJECT_STATE.md
- docs/TASKS.md
- docs/RELEASE_GATES.md

Portable test evidence: copied byte-for-byte into the ignored main-checkout
frontend/test-results/free-pr-check directory solely to reuse installed modules.
No install. Focused strict TypeScript exit 0; both browser tests pass, no skips,
6.3 s, against the existing 0.1 CPU container. Node emitted the benign existing
NO_COLOR/FORCE_COLOR warning; no application error. Exact commands from frontend:

```powershell
node node_modules/typescript/bin/tsc -p test-results/free-pr-check/tsconfig.demo-check.json
npm.cmd --offline --cache=C:\AI\Projects\FIS4\.harness-test-tmp\npm-cache run test:e2e -- --config=test-results/free-pr-check/playwright.demo.config.ts --output=../.harness-test-tmp/demo-evidence/free-portable-browser-results
```

Raw logs, screenshots, inventories, host probes, patches, node_modules and original
POC spec stay outside publication. Nothing staged. Final whitespace, protected-file,
original-POC-hash and explicit untracked security checks are recorded in project
state. No full test suites or image builds repeated.

Remaining gates: review/publication and hosted exposure approval; actual Render
build/new-deploy/idle-wake acceptance; CVE/supply-chain review (the regex scanner
is not that review); physical-device/iOS testing; separate Windows offline exact
package acceptance. No SQL/ML or production acceptance. Linux demo paths/lock are
isolated from unchanged canonical Windows dependencies and FIS-002 requirements.

Final Free-follow-up checks: security exit 0, 71 tracked/index files, zero confirmed
violations; ten unchanged benign manual leads retain their dispositions above.
Eight untracked files explicitly inspected with the same rules: zero extra leads.
Tracked/untracked whitespace, empty index and all five original POC hashes PASS.
Only three governance files have tracked changes; backend, React application,
simulator, formulas, decisions and canonical dependencies remain unchanged.
Eleven pending files include the old local-only POC spec; PR allowlist is ten.
