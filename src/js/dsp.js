// Pure DSP + axis math. No DOM. Reference: design/build_mocks.py (coeffs, band_db).

export const FMIN = 20;
export const FMAX = 20000;
export const FS = 48000;

const LOG_RANGE = Math.log(FMAX / FMIN);

export function clampFreq(f) {
  if (!Number.isFinite(f)) return 1000;
  return Math.min(FMAX, Math.max(FMIN, f));
}

export function freqToX(f, width) {
  return (width * Math.log(clampFreq(f) / FMIN)) / LOG_RANGE;
}

export function xToFreq(x, width) {
  const t = Math.min(1, Math.max(0, x / width));
  return FMIN * Math.exp(t * LOG_RANGE);
}

// RBJ Audio EQ Cookbook, Q form. Returns unnormalised coefficients.
export function coeffs(band) {
  const A = Math.pow(10, band.gain / 40);
  const w0 = (2 * Math.PI * band.fc) / FS;
  const c = Math.cos(w0);
  const s = Math.sin(w0);
  const al = s / (2 * band.q);
  if (band.type === 'PK') {
    return { b0: 1 + al * A, b1: -2 * c, b2: 1 - al * A, a0: 1 + al / A, a1: -2 * c, a2: 1 - al / A };
  }
  const sa = 2 * Math.sqrt(A) * al;
  if (band.type === 'LSC') {
    return {
      b0: A * ((A + 1) - (A - 1) * c + sa),
      b1: 2 * A * ((A - 1) - (A + 1) * c),
      b2: A * ((A + 1) - (A - 1) * c - sa),
      a0: (A + 1) + (A - 1) * c + sa,
      a1: -2 * ((A - 1) + (A + 1) * c),
      a2: (A + 1) + (A - 1) * c - sa,
    };
  }
  // HSC
  return {
    b0: A * ((A + 1) + (A - 1) * c + sa),
    b1: -2 * A * ((A - 1) + (A + 1) * c),
    b2: A * ((A + 1) + (A - 1) * c - sa),
    a0: (A + 1) - (A - 1) * c + sa,
    a1: 2 * ((A - 1) - (A + 1) * c),
    a2: (A + 1) - (A - 1) * c - sa,
  };
}

export function magnitudeDb(band, f) {
  const { b0, b1, b2, a0, a1, a2 } = coeffs(band);
  const w = (2 * Math.PI * f) / FS;
  const cw = Math.cos(w), sw = Math.sin(w), c2w = Math.cos(2 * w), s2w = Math.sin(2 * w);
  const nr = b0 + b1 * cw + b2 * c2w, ni = -b1 * sw - b2 * s2w;
  const dr = a0 + a1 * cw + a2 * c2w, di = -a1 * sw - a2 * s2w;
  const num = nr * nr + ni * ni;
  const den = dr * dr + di * di;
  return 10 * Math.log10(num / den);
}

export function responseDb(bands, f) {
  let sum = 0;
  for (const b of bands) if (b.enabled !== false) sum += magnitudeDb(b, f);
  return sum;
}

// Log-spaced sample frequencies for drawing curves.
export function sampleFreqs(n = 320) {
  const out = new Array(n);
  for (let i = 0; i < n; i++) out[i] = FMIN * Math.pow(FMAX / FMIN, i / (n - 1));
  return out;
}

export function bandFromMarks(draft) {
  const { start, top, end, kind } = draft;
  let fc;
  if (top != null) fc = top;
  else if (start != null && end != null) fc = Math.sqrt(start * end);
  else return null;
  let q = 2.0;
  if (start != null && end != null && Math.abs(end - start) > 0) {
    q = fc / Math.abs(end - start);
  }
  q = Math.min(10, Math.max(0.3, q));
  q = Math.round(q * 20) / 20;
  return { type: 'PK', fc: Math.round(fc), gain: kind === 'dip' ? 3 : -3, q };
}

export function autoPreamp(bands) {
  let maxBoost = 0;
  for (const b of bands) if (b.enabled !== false && b.gain > maxBoost) maxBoost = b.gain;
  return -Math.round(maxBoost * 10) / 10;
}

// "3 100" with a thin space (U+2009) as thousands separator, integer Hz.
export function fmtHz(f) {
  const n = Math.round(f);
  const s = String(Math.abs(n));
  const parts = [];
  for (let i = s.length; i > 0; i -= 3) parts.unshift(s.slice(Math.max(0, i - 3), i));
  return (n < 0 ? '-' : '') + parts.join(' ');
}

// Tick labels: 105 → "105", 2500 → "2.5k", 20000 → "20k".
export function fmtK(f) {
  if (f >= 1000) {
    const v = f / 1000;
    return `${Number.isInteger(v) ? v : Number(v.toFixed(2))}k`;
  }
  return String(Math.round(f));
}

export const MAJOR_TICKS = [20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000];
export const MINOR_TICKS = [30, 40, 60, 70, 80, 90, 300, 400, 600, 700, 800, 900, 3000, 4000, 6000, 7000, 8000, 9000];
