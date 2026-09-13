import { toPeqText } from './export.js';

const tauri = () => (typeof window !== 'undefined' ? window.__TAURI__ : undefined);

export function isDesktop() {
  return !!tauri();
}

async function invoke(cmd, args) {
  const t = tauri();
  if (!t) throw new Error('Not running inside the desktop shell.');
  return t.core.invoke(cmd, args);
}

export const detectConfigDir = () => invoke('detect_apo_config_dir');
export const getSettings = () => invoke('get_apo_settings');
export const saveSettings = (settings) => invoke('save_apo_settings', { settings });
export const ensureIncludeDirective = (configDir) => invoke('ensure_include_directive', { configDir });
export const writePreset = (configDir, content) => invoke('write_eqbyear_preset', { configDir, content });
export const checkStatus = (configDir) => invoke('check_apo_status', { configDir });

export async function pickConfigDir() {
  const t = tauri();
  if (!t) return null;
  const dir = await t.dialog.open({ directory: true, title: 'Select the EqualizerAPO config folder' });
  return typeof dir === 'string' ? dir : null;
}

// EqualizerAPO expects Preamp <= 0; only the file written for it is clamped.
function toApoText(state) {
  const clamped = { ...state, preampDb: Math.min(0, Number(state.preampDb) || 0) };
  return toPeqText(clamped);
}

export function createApoSync(store, { delay = 400 } = {}) {
  let timer = null;
  let lastError = null;
  let lastWriteAt = null;
  const listeners = new Set();
  const notify = () => {
    for (const fn of listeners) fn({ lastError, lastWriteAt });
  };

  async function flush() {
    let settings;
    try {
      settings = await getSettings();
    } catch (e) {
      return; // no desktop shell, or not ready yet
    }
    if (!settings || !settings.sync_enabled || !settings.config_dir) return;
    try {
      await writePreset(settings.config_dir, toApoText(store.get()));
      lastError = null;
      lastWriteAt = Date.now();
    } catch (e) {
      lastError = String(e && e.message ? e.message : e);
    }
    notify();
  }

  return {
    onStateChange() {
      if (!isDesktop()) return;
      clearTimeout(timer);
      timer = setTimeout(flush, delay);
    },
    onStatus(fn) {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    flushNow: flush,
  };
}
