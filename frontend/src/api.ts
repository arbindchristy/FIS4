/** API-owned metrics only. This module validates contracts; it calculates no readiness. */
export type Source = 'synthetic' | 'sql';
export type Filters = { date: string; command: string };
export const STATUSES = ['FMC', 'PMCM', 'PMCS', 'NMCS', 'NMCM', 'DEPOT'] as const;
const countKeys = ['total_tails', 'fmc_tails', 'pmc_tails', 'nmcs_tails', 'nmcm_tails', 'depot_tails'] as const;
export type Metrics = Record<(typeof countKeys)[number], number> & { svc_pct: number; avail_pct: number };
type Metadata = { source: Source; date: string; command: string | null };
export type Fleet = Metadata & { metrics: Metrics };
export type Commands = Metadata & { commands: (Metrics & { command: string })[] };
export type Distribution = Metadata & { total_tails: number; statuses: { status: string; count: number; pct: number }[] };
type Snapshot = { fleet: Fleet; commands: Commands; distribution: Distribution };
export type Dashboard = Snapshot & { availableCommands: string[]; overall?: Snapshot };
export type FailureKind = 'empty' | 'invalid' | 'unavailable' | 'contract' | 'source' | 'unsupported';

export class DashboardError extends Error {
  constructor(public readonly kind: FailureKind, message: string, public readonly source?: Source) {
    super(message);
    this.name = 'DashboardError';
  }
}

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const isSource = (value: unknown): value is Source => value === 'synthetic' || value === 'sql';
const isCount = (value: unknown): value is number => typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
const isPercentage = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100;
const commandPattern = /^[A-Z0-9_-]{1,32}$/;
const isCommand = (value: unknown): value is string => typeof value === 'string' && commandPattern.test(value);

export function validDate(value: string): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || value.startsWith('0000')) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

function contract(): never {
  throw new DashboardError('contract', 'The API returned an unexpected response. No readiness data is displayed.');
}

function metadata(value: unknown): asserts value is Record<string, unknown> & Metadata {
  if (!isObject(value) || !isSource(value.source) || typeof value.date !== 'string' || !validDate(value.date)
      || (value.command !== null && !isCommand(value.command))) contract();
}

function metrics(value: unknown): asserts value is Metrics {
  if (!isObject(value) || !countKeys.every(key => isCount(value[key]))
      || !isPercentage(value.svc_pct) || !isPercentage(value.avail_pct)) contract();
}

function fleet(value: unknown): Fleet {
  metadata(value);
  metrics(value.metrics);
  return value as unknown as Fleet;
}

function commands(value: unknown): Commands {
  metadata(value);
  if (!Array.isArray(value.commands)) contract();
  for (const row of value.commands) {
    metrics(row);
    if (!isCommand((row as Record<string, unknown>).command)) contract();
  }
  if (new Set(value.commands.map(row => row.command)).size !== value.commands.length) contract();
  return value as unknown as Commands;
}

function distribution(value: unknown): Distribution {
  metadata(value);
  if (!isCount(value.total_tails) || !Array.isArray(value.statuses)) contract();
  for (const row of value.statuses) {
    if (!isObject(row) || typeof row.status !== 'string' || !row.status.trim()
        || !isCount(row.count) || !isPercentage(row.pct)) contract();
  }
  const codes = value.statuses.map(row => row.status);
  if (new Set(codes).size !== codes.length || !STATUSES.every(code => codes.includes(code))) contract();
  return value as unknown as Distribution;
}

/** Bound platform JSON before parsing, including responses without Content-Length. */
async function boundedJson(response: Response, maxBytes: number): Promise<unknown> {
  const declared = response.headers.get('Content-Length');
  if (declared !== null && (!/^[0-9]+$/.test(declared) || Number(declared) > maxBytes)) contract();
  const reader = response.body?.getReader();
  if (!reader) contract();
  let bytes = 0;
  let text = '';
  const decoder = new TextDecoder();
  try {
    while (true) {
      const chunk = await reader.read();
      if (chunk.done) break;
      bytes += chunk.value.byteLength;
      if (bytes > maxBytes) { await reader.cancel(); contract(); }
      text += decoder.decode(chunk.value, { stream: true });
    }
    return JSON.parse(text + decoder.decode()) as unknown;
  } finally { reader.releaseLock(); }
}

/** Only same-origin fixed paths are used; no credentials, external URL or provider selector. */
async function request(path: string, signal: AbortSignal, reportSource: (source: Source) => void, maxBytes?: number): Promise<unknown> {
  if (signal.aborted) throw new DOMException('Request cancelled', 'AbortError');
  const controller = new AbortController();
  const abort = () => controller.abort();
  if (signal.aborted) controller.abort();
  signal.addEventListener('abort', abort, { once: true });
  const timer = setTimeout(abort, 15000);
  try {
    const response = await fetch(path, {
      signal: controller.signal, credentials: 'omit', cache: 'no-store', redirect: 'error',
      headers: { Accept: 'application/json' },
    });
    const header = response.headers.get('X-FIS4-Data-Source');
    if (isSource(header)) reportSource(header);
    if (header === 'sql') throw new DashboardError('source', 'SQL is configured. This demonstration accepts synthetic data only.', 'sql');
    let body: unknown;
    try { body = maxBytes === undefined ? await response.json() : await boundedJson(response, maxBytes); } catch { contract(); }
    if (signal.aborted) throw new DOMException('Request cancelled', 'AbortError');
    const source = isObject(body) && isSource(body.source) ? body.source : isSource(header) ? header : undefined;
    if (source) reportSource(source);
    if (source === 'sql' || header === 'sql') {
      reportSource('sql');
      throw new DashboardError('source', 'SQL is configured. This demonstration accepts synthetic data only; no further data requests will be made.', 'sql');
    }
    if (maxBytes !== undefined && response.ok && header !== 'synthetic') contract();
    if (header !== null && (!isSource(header) || (isObject(body) && body.source !== undefined && body.source !== header))) contract();
    if (!response.ok) {
      if ((path.startsWith('/api/v1/readiness/history/series?') || path.startsWith('/api/v1/platforms')
          || path.startsWith('/api/v1/readiness/history/platforms')) && response.status === 404
          && header === 'synthetic' && isObject(body) && body.detail === 'Not Found') {
        throw new DashboardError('unsupported', 'Historical trends are not enabled for this provider. Snapshot controls remain available.', source);
      }
      if (response.status === 404) throw new DashboardError('empty', 'No readiness snapshot matches these filters. Choose another date or reset to the latest snapshot.', source);
      if (response.status === 422) throw new DashboardError('invalid', 'The API rejected these filters. Check the date and command, then apply again.', source);
      throw new DashboardError('unavailable', 'The readiness API is unavailable. Check the local backend and try again.', source);
    }
    if (!isObject(body) || !isSource(body.source)) contract();
    return body;
  } catch (error) {
    if (signal.aborted) throw new DOMException('Request cancelled', 'AbortError');
    if (error instanceof DashboardError) throw error;
    throw new DashboardError('unavailable', 'The readiness API could not be reached or timed out. Check the local backend and try again.');
  } finally {
    clearTimeout(timer);
    signal.removeEventListener('abort', abort);
  }
}

function query(filters: Filters): string {
  const params = new URLSearchParams();
  if (filters.date) params.set('date', filters.date);
  if (filters.command) params.set('command', filters.command);
  const value = params.toString();
  return value ? `?${value}` : '';
}

export async function loadDashboard(filters: Filters, signal: AbortSignal, reportSource: (source: Source) => void): Promise<Dashboard> {
  if ((filters.date && !validDate(filters.date)) || (filters.command && !isCommand(filters.command))) {
    throw new DashboardError('invalid', 'Enter a valid calendar date and select a valid command.');
  }
  // Liveness is safe in either mode. Refuse SQL before any aggregate request.
  const health = await request('/health', signal, reportSource);
  if (!isObject(health) || health.status !== 'ok' || health.source !== 'synthetic') contract();
  const allCommands = commands(await request(`/api/v1/readiness/commands${query({ ...filters, command: '' })}`, signal, reportSource));
  if (allCommands.command !== null || (filters.date && allCommands.date !== filters.date)) contract();
  // Pin every metric request to the API's returned date, including initial latest selection.
  const resolved = { date: allCommands.date, command: filters.command };
  const suffix = query(resolved);
  const [selectedFleet, selectedDistribution, selectedCommands] = await Promise.all([
    request(`/api/v1/readiness/fleet${suffix}`, signal, reportSource).then(fleet),
    request(`/api/v1/status-distribution${suffix}`, signal, reportSource).then(distribution),
    filters.command ? request(`/api/v1/readiness/commands${suffix}`, signal, reportSource).then(commands) : Promise.resolve(allCommands),
  ]);
  for (const report of [selectedFleet, selectedDistribution, selectedCommands]) {
    if (report.date !== resolved.date || report.command !== (filters.command || null) || report.source !== 'synthetic') contract();
  }
  if (selectedFleet.metrics.total_tails === 0 || selectedCommands.commands.length === 0) {
    throw new DashboardError('empty', 'The API returned an empty snapshot. Choose another date or command.', 'synthetic');
  }
  const overall = filters.command ? {
    fleet: fleet(await request(`/api/v1/readiness/fleet?date=${resolved.date}`, signal, reportSource)),
    distribution: distribution(await request(`/api/v1/status-distribution?date=${resolved.date}`, signal, reportSource)),
    commands: allCommands,
  } : { fleet: selectedFleet, distribution: selectedDistribution, commands: allCommands };
  for (const report of [overall.fleet, overall.distribution, overall.commands]) {
    if (report.source !== 'synthetic' || report.date !== resolved.date || report.command !== null) contract();
  }
  if (!countKeys.every(key => allCommands.commands.reduce((sum, row) => sum + row[key], 0) === overall.fleet.metrics[key])) contract();
  validateDistribution(overall.fleet, overall.distribution);
  if (filters.command) {
    const row = allCommands.commands.find(row => row.command === filters.command);
    if (!row || selectedCommands.commands.length !== 1 || selectedCommands.commands[0].command !== filters.command
        || ![...countKeys, 'svc_pct', 'avail_pct'].every(key => row[key as keyof Metrics] === selectedFleet.metrics[key as keyof Metrics]
          && row[key as keyof Metrics] === selectedCommands.commands[0][key as keyof Metrics])) contract();
  }
  validateDistribution(selectedFleet, selectedDistribution);
  return { fleet: selectedFleet, commands: selectedCommands, distribution: selectedDistribution, overall,
    availableCommands: allCommands.commands.map(row => row.command) };
}

function validateDistribution(report: Fleet, counts: Distribution) {
  if (counts.source !== report.source || counts.date !== report.date || counts.command !== report.command
      || counts.total_tails !== report.metrics.total_tails || counts.statuses.length !== 6) contract();
  const byCode = Object.fromEntries(counts.statuses.map(row => [row.status, row.count]));
  if (STATUSES.reduce((sum, code) => sum + byCode[code], 0) !== report.metrics.total_tails
      || byCode.FMC !== report.metrics.fmc_tails || byCode.PMCM + byCode.PMCS !== report.metrics.pmc_tails
      || byCode.NMCS !== report.metrics.nmcs_tails || byCode.NMCM !== report.metrics.nmcm_tails
      || byCode.DEPOT !== report.metrics.depot_tails) contract();
}

/** Obtain the six-status partition for one API-owned command summary, without deriving percentages. */
export async function loadCommandSnapshot(snapshot: Dashboard, row: Commands['commands'][number], signal: AbortSignal,
  reportSource: (source: Source) => void): Promise<Dashboard> {
  if (snapshot.fleet.source !== 'synthetic' || !validDate(snapshot.fleet.date) || !isCommand(row.command)
      || !snapshot.commands.commands.includes(row)) contract();
  const params = new URLSearchParams({ date: snapshot.fleet.date, command: row.command });
  const counts = distribution(await request(`/api/v1/status-distribution?${params}`, signal, reportSource));
  const report: Fleet = { source: 'synthetic', date: snapshot.fleet.date, command: row.command, metrics: row };
  validateDistribution(report, counts);
  return { fleet: report, distribution: counts, commands: { ...snapshot.commands, command: row.command, commands: [row] },
    availableCommands: snapshot.availableCommands };
}

export const WINDOWS = [30, 90, 180, 365] as const;
export type HistoryWindow = (typeof WINDOWS)[number];
export type Observation = Metrics & { date: string; status_counts: Record<(typeof STATUSES)[number], number> };
export type HistorySeries = { source: 'synthetic'; command: string | null; requested_days: HistoryWindow;
  start_date: string; end_date: string; point_count: number; observations: Observation[] };
const dayMillis = 86400000;

/** Validate observations and selection consistency, never recompute readiness percentages. */
export async function loadSeries(snapshot: Dashboard, days: HistoryWindow, signal: AbortSignal,
  reportSource: (source: Source) => void): Promise<HistorySeries> {
  if (!WINDOWS.includes(days) || !validDate(snapshot.fleet.date) || snapshot.fleet.source !== 'synthetic') contract();
  const params = new URLSearchParams({ end_date: snapshot.fleet.date, days: String(days) });
  if (snapshot.fleet.command) params.set('command', snapshot.fleet.command);
  const value = await request(`/api/v1/readiness/history/series?${params}`, signal, reportSource);
  if (!isObject(value) || value.source !== 'synthetic' || value.command !== snapshot.fleet.command
      || value.requested_days !== days || value.end_date !== snapshot.fleet.date
      || typeof value.start_date !== 'string' || !validDate(value.start_date)
      || !isCount(value.point_count) || !Array.isArray(value.observations)) contract();
  if (value.observations.length === 0) throw new DashboardError('empty', 'No historical observations were returned for this period.', 'synthetic');
  const span = (Date.parse(value.end_date as string) - Date.parse(value.start_date)) / dayMillis + 1;
  if (value.point_count !== value.observations.length || span !== value.point_count || span < 1 || span > days) contract();
  for (const [index, point] of value.observations.entries()) {
    metrics(point);
    const row = point as unknown as Record<string, unknown>;
    const expectedDay = new Date(Date.parse(value.start_date) + index * dayMillis).toISOString().slice(0, 10);
    if (row.date !== expectedDay || point.total_tails !== (value.command === null ? 160 : 40)
        || !isObject(row.status_counts) || Object.keys(row.status_counts).length !== 6) contract();
    const counts = row.status_counts;
    if (!STATUSES.every(code => isCount(counts[code]) && counts[code] <= 160)
        || STATUSES.reduce((sum, code) => sum + (counts[code] as number), 0) !== point.total_tails
        || counts.FMC !== point.fmc_tails || counts.NMCS !== point.nmcs_tails
        || counts.NMCM !== point.nmcm_tails || counts.DEPOT !== point.depot_tails
        || (counts.PMCM as number) + (counts.PMCS as number) !== point.pmc_tails) contract();
  }
  const series = value as unknown as HistorySeries;
  const last = series.observations[series.observations.length - 1];
  if (![...countKeys, 'svc_pct', 'avail_pct'].every(key =>
    Math.abs(last[key as keyof Metrics] - snapshot.fleet.metrics[key as keyof Metrics]) < 1e-8)) contract();
  if (!STATUSES.every(code => last.status_counts[code] === snapshot.distribution.statuses.find(row => row.status === code)?.count)) contract();
  return series;
}


export type PlatformRow = Metrics & { platform: string; status_counts: Observation['status_counts'] };
export type PlatformData = { options: string[]; rows: PlatformRow[] };
export type PlatformSeries = HistorySeries & { platform: string };
const platformPattern = /^[A-Z0-9][A-Z0-9-]{0,31}$/;
const isPlatform = (value: unknown): value is string => typeof value === 'string' && platformPattern.test(value);
const platformBytes = 262144;
const metricKeys = [...countKeys, 'svc_pct', 'avail_pct'] as const;

function keys(value: Record<string, unknown>, expected: readonly string[]) {
  if (Object.keys(value).length !== expected.length || !expected.every(key => Object.hasOwn(value, key))) contract();
}

function canonicalCounts(value: unknown): asserts value is Metrics & Record<string, unknown> & { status_counts: Observation['status_counts'] } {
  metrics(value);
  const row = value as Metrics & Record<string, unknown>;
  if (!isObject(row.status_counts)) contract();
  const counts = row.status_counts;
  keys(counts, STATUSES);
  if (!STATUSES.every(code => isCount(counts[code]) && counts[code] <= row.total_tails)
      || STATUSES.reduce((sum, code) => sum + (counts[code] as number), 0) !== row.total_tails
      || counts.FMC !== row.fmc_tails || counts.NMCS !== row.nmcs_tails
      || counts.NMCM !== row.nmcm_tails || counts.DEPOT !== row.depot_tails
      || (counts.PMCM as number) + (counts.PMCS as number) !== row.pmc_tails) contract();
}

function platformSnapshot(snapshot: Dashboard) {
  if (snapshot.fleet.source !== 'synthetic' || !validDate(snapshot.fleet.date)
      || (snapshot.fleet.command !== null && !isCommand(snapshot.fleet.command))) contract();
}

/** Counts reconcile to the actual selected snapshot; no synthetic population constants or percentage formulas. */
export async function loadPlatforms(snapshot: Dashboard, signal: AbortSignal,
  reportSource: (source: Source) => void): Promise<PlatformData> {
  platformSnapshot(snapshot);
  const list = new URLSearchParams();
  if (snapshot.fleet.command) list.set('command', snapshot.fleet.command);
  const comparison = new URLSearchParams({ date: snapshot.fleet.date });
  if (snapshot.fleet.command) comparison.set('command', snapshot.fleet.command);
  const [options, report] = await Promise.all([
    request(`/api/v1/platforms${list.size ? `?${list}` : ''}`, signal, reportSource, platformBytes),
    request(`/api/v1/readiness/history/platforms?${comparison}`, signal, reportSource, platformBytes),
  ]);
  if (!isObject(options) || options.source !== 'synthetic' || options.command !== snapshot.fleet.command
      || !Array.isArray(options.platforms) || options.platforms.length > 32) contract();
  keys(options, ['source', 'command', 'platforms']);
  const labels = options.platforms;
  if (!labels.every(isPlatform) || new Set(labels).size !== labels.length
      || labels.some((label, index) => index > 0 && label <= labels[index - 1])) contract();
  metadata(report);
  keys(report, ['source', 'date', 'command', 'platform', 'platforms']);
  if (report.source !== 'synthetic' || report.date !== snapshot.fleet.date
      || report.command !== snapshot.fleet.command || report.platform !== null
      || !Array.isArray(report.platforms) || report.platforms.length > 32) contract();
  if (!labels.length && !report.platforms.length) throw new DashboardError('empty', 'No platform observations are available.');
  const rows = report.platforms.map(value => {
    if (!isObject(value)) contract();
    keys(value, ['platform', ...metricKeys, 'status_counts']);
    canonicalCounts(value);
    if (!isPlatform(value.platform)) contract();
    return value as PlatformRow;
  });
  if (rows.length !== labels.length || new Set(rows.map(row => row.platform)).size !== rows.length
      || !labels.every(label => rows.some(row => row.platform === label))) contract();
  if (!countKeys.every(key => rows.reduce((sum, row) => sum + row[key], 0) === snapshot.fleet.metrics[key])
      || snapshot.distribution.total_tails !== snapshot.fleet.metrics.total_tails
      || snapshot.distribution.date !== snapshot.fleet.date || snapshot.distribution.command !== snapshot.fleet.command
      || !STATUSES.every(code => rows.reduce((sum, row) => sum + row.status_counts[code], 0)
        === snapshot.distribution.statuses.find(row => row.status === code)?.count)) contract();
  return { options: labels, rows };
}

export async function loadPlatformSeries(snapshot: Dashboard, selected: PlatformRow, days: HistoryWindow,
  signal: AbortSignal, reportSource: (source: Source) => void): Promise<PlatformSeries> {
  platformSnapshot(snapshot);
  if (!isPlatform(selected.platform) || !WINDOWS.includes(days)) contract();
  const params = new URLSearchParams({ end_date: snapshot.fleet.date, days: String(days), platform: selected.platform });
  if (snapshot.fleet.command) params.set('command', snapshot.fleet.command);
  const value = await request(`/api/v1/readiness/history/platforms/series?${params}`, signal, reportSource, platformBytes);
  if (!isObject(value)) contract();
  keys(value, ['source', 'command', 'requested_days', 'start_date', 'end_date', 'point_count', 'observations', 'platform']);
  if (value.source !== 'synthetic' || value.command !== snapshot.fleet.command || value.platform !== selected.platform
      || value.requested_days !== days || value.end_date !== snapshot.fleet.date
      || typeof value.start_date !== 'string' || !validDate(value.start_date)
      || !isCount(value.point_count) || !Array.isArray(value.observations) || value.observations.length > 365) contract();
  if (!value.observations.length) throw new DashboardError('empty', 'No platform history is available.');
  const span = (Date.parse(snapshot.fleet.date) - Date.parse(value.start_date)) / dayMillis + 1;
  if (span !== value.point_count || span !== value.observations.length || span < 1 || span > days) contract();
  for (const [index, point] of value.observations.entries()) {
    if (!isObject(point)) contract();
    keys(point, [...metricKeys, 'date', 'status_counts']);
    canonicalCounts(point);
    if (point.date !== new Date(Date.parse(value.start_date) + index * dayMillis).toISOString().slice(0, 10)) contract();
  }
  const series = value as unknown as PlatformSeries;
  const last = series.observations.at(-1)!;
  if (!metricKeys.every(key => Math.abs(last[key] - selected[key]) < 1e-8)
      || !STATUSES.every(code => last.status_counts[code] === selected.status_counts[code])) contract();
  return series;
}
