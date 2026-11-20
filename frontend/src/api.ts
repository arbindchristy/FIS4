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
export type Dashboard = { fleet: Fleet; commands: Commands; distribution: Distribution; availableCommands: string[] };
export type FailureKind = 'empty' | 'invalid' | 'unavailable' | 'contract' | 'source';

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

/** Only same-origin fixed paths are used; no credentials, external URL or provider selector. */
async function request(path: string, signal: AbortSignal, reportSource: (source: Source) => void): Promise<unknown> {
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
    let body: unknown;
    try { body = await response.json(); } catch { contract(); }
    if (signal.aborted) throw new DOMException('Request cancelled', 'AbortError');
    const source = isObject(body) && isSource(body.source) ? body.source : isSource(header) ? header : undefined;
    if (source) reportSource(source);
    if (source === 'sql' || header === 'sql') {
      reportSource('sql');
      throw new DashboardError('source', 'SQL is configured. This demonstration accepts synthetic data only; no further data requests will be made.', 'sql');
    }
    if (header !== null && (!isSource(header) || (isObject(body) && body.source !== undefined && body.source !== header))) contract();
    if (!response.ok) {
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
  return { fleet: selectedFleet, commands: selectedCommands, distribution: selectedDistribution,
    availableCommands: allCommands.commands.map(row => row.command) };
}
