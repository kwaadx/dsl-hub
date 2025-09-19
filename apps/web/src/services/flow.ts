export interface Flow {
  id: string;
  name: string;
}

export interface Paged<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

/** Simple UUID (for newly created items). */
function uuid(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
}

/** Cancellable delay helper using AbortSignal. */
function delay(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    if (signal) {
      const onAbort = () => {
        clearTimeout(t);
        const err = new Error('Aborted');
        // @ts-ignore
        err.name = 'AbortError';
        reject(err);
      };
      if (signal.aborted) return onAbort();
      signal.addEventListener('abort', onAbort, { once: true });
    }
  });
}

/** Deterministic hash-based id from name (stable across reloads). */
function stableIdFromName(name: string): string {
  // djb2 (xor) hash — fast and stable
  let h = 5381;
  const s = name.toLowerCase();
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h) ^ s.charCodeAt(i);
  const hex = (h >>> 0).toString(16).padStart(8, '0');
  return `flow-${hex}`;
}

/** Seed names for the fake dataset. */
const SEED_NAMES = [
  'Pipeline Agent — Alpha',
  'ROS2 Sensors Group',
  'Outreach — Appliance',
  'ETL — Events Ingest',
  'LLM Playground',
  'Vision — OCR Pipeline',
  'Telemetry — Realtime',
  'QA — Regression Suite',
  'Scheduler — Cron Jobs',
  'Sandbox — Experiments',
] as const;

/** Default (seed) dataset with stable ids derived from names. */
const DEFAULT_FLOWS: Flow[] = SEED_NAMES.map((name) => ({
  id: stableIdFromName(name),
  name,
}));

/** LocalStorage persistence (per-browser). */
const LS_KEY = 'dslhub_fake_flows_v1';

function canUseLS(): boolean {
  try {
    return typeof window !== 'undefined' && !!window.localStorage;
  } catch {
    return false;
  }
}
function loadFromLS(): Flow[] | null {
  if (!canUseLS()) return null;
  const raw = localStorage.getItem(LS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Flow[];
    if (!Array.isArray(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}
function saveToLS(data: Flow[]) {
  if (!canUseLS()) return;
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(data));
  } catch {
    // ignore quota/security errors in fake mode
  }
}

/** In-memory DB (seeded from LS or defaults). */
let DB: Flow[] = loadFromLS() ?? DEFAULT_FLOWS.slice();
if (loadFromLS() == null) {
  // Seed LS on first run so ids stay stable across reloads
  saveToLS(DB);
}

/** Public helpers to reset/inspect fake DB (optional). */
export function __resetFakeFlows() {
  DB = DEFAULT_FLOWS.slice();
  saveToLS(DB);
}
export function __getFakeFlows(): Flow[] {
  return DB.map((f) => ({ ...f }));
}

/** Fetch all flows. */
export async function fetchFlowsApi(signal?: AbortSignal): Promise<Flow[]> {
  await delay(300 + Math.floor(Math.random() * 300), signal);

  // throw new Error('Test error in fetchFlowsApi');
  return DB.map((f) => ({ ...f }));
}

/** Fetch single flow by id. */
export async function fetchFlowByIdApi(id: string, signal?: AbortSignal): Promise<Flow> {
  await delay(200 + Math.floor(Math.random() * 200), signal);
  const found = DB.find((f) => f.id === id);
  if (!found) {
    const err = new Error('Flow not found') as Error & { status?: number };
    err.status = 404;
    throw err;
  }
  return { ...found };
}

/** Create flow (persist to LS). */
export async function createFlowApi(payload: { name: string }, signal?: AbortSignal): Promise<Flow> {
  await delay(200 + Math.floor(Math.random() * 300), signal);
  const item: Flow = { id: uuid(), name: payload.name };
  DB.unshift(item);
  saveToLS(DB);
  return { ...item };
}

/** Update flow (persist to LS). */
export async function updateFlowApi(id: string, patch: Partial<Flow>, signal?: AbortSignal): Promise<Flow> {
  await delay(200 + Math.floor(Math.random() * 300), signal);
  const idx = DB.findIndex((f) => f.id === id);
  if (idx === -1) {
    const err = new Error('Flow not found') as Error & { status?: number };
    err.status = 404;
    throw err;
  }
  DB[idx] = { ...DB[idx], ...patch };
  saveToLS(DB);
  return { ...DB[idx] };
}

/** Delete flow (persist to LS). */
export async function deleteFlowApi(id: string, signal?: AbortSignal): Promise<void> {
  await delay(150 + Math.floor(Math.random() * 200), signal);
  const idx = DB.findIndex((f) => f.id === id);
  if (idx !== -1) {
    DB.splice(idx, 1);
    saveToLS(DB);
  }
}

/** Paged fetch with optional search (persisted DB). */
export async function fetchFlowsPagedApi(
  params: { page: number; pageSize?: number; q?: string },
  signal?: AbortSignal
): Promise<Paged<Flow>> {
  const { page, pageSize = 5, q = '' } = params;
  await delay(250 + Math.floor(Math.random() * 250), signal);

  const needle = q.trim().toLowerCase();
  const filtered = needle ? DB.filter((f) => f.name.toLowerCase().includes(needle)) : DB;

  const start = Math.max(0, (page - 1) * pageSize);
  const items = filtered.slice(start, start + pageSize).map((f) => ({ ...f }));

  const totalItems = filtered.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  return { items, page, pageSize, totalItems, totalPages };
}
