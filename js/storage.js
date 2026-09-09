// localStorage autosave/restore. Every failure is silent.

export const KEY = 'dms-sweep:v1';
const DELAY = 300;

let timer = null;
let pending = null;

function store() {
  try {
    return globalThis.localStorage || null;
  } catch (e) {
    return null;
  }
}

function persist(state) {
  try {
    const ls = store();
    if (!ls) return;
    const { playing, ...rest } = state;
    ls.setItem(KEY, JSON.stringify(rest));
  } catch (e) {
    /* quota, private mode, disabled storage — ignore */
  }
}

// Debounced 300 ms. All fields except `playing`.
export function save(state) {
  pending = state;
  if (timer !== null) clearTimeout(timer);
  timer = setTimeout(() => {
    timer = null;
    const s = pending;
    pending = null;
    if (s) persist(s);
  }, DELAY);
}

// Write immediately (used on pagehide).
export function flush() {
  if (timer !== null) {
    clearTimeout(timer);
    timer = null;
  }
  const s = pending;
  pending = null;
  if (s) persist(s);
}

export function load() {
  try {
    const ls = store();
    if (!ls) return null;
    const raw = ls.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
    return data;
  } catch (e) {
    return null;
  }
}

export function clear() {
  try {
    const ls = store();
    if (ls) ls.removeItem(KEY);
  } catch (e) {
    /* ignore */
  }
}
