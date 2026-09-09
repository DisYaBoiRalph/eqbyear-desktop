// Checks js/dsp.js against reference numbers produced by design/build_mocks.py
// (xlog, coeffs, band_db). Run:  node tests/dsp.test.mjs
// Exits non-zero on the first failing assertion group.

import {
  freqToX, xToFreq, magnitudeDb, bandFromMarks, autoPreamp, fmtHz, fmtK,
} from '../js/dsp.js';

let failures = 0;
let checks = 0;

function ok(name, pass, detail) {
  checks++;
  if (pass) {
    console.log(`  ok   ${name}`);
  } else {
    failures++;
    console.log(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`);
  }
}

function near(name, actual, expected, tol) {
  const d = Math.abs(actual - expected);
  ok(name, d <= tol, `got ${actual}, expected ${expected} (|Δ| ${d.toExponential(3)} > ${tol})`);
}

function eq(name, actual, expected) {
  ok(name, Object.is(actual, expected), `got ${JSON.stringify(actual)}, expected ${JSON.stringify(expected)}`);
}

const TOL_DB = 1e-6;

// ---- magnitudeDb vs. build_mocks.band_db ----------------------------------
// Values printed by python3 using the reference implementation verbatim.
const MAG_CASES = [
  ['PK 3100 -4.5 q2.6', { type: 'PK', fc: 3100, gain: -4.5, q: 2.6 }, [
    [3100, -4.500000000000003],
    [2500, -1.9382854628399797],
    [3750, -2.1842670925242516],
    [1000, -0.08568362244277694],
  ]],
  ['LSC 105 +2.0 q0.7', { type: 'LSC', fc: 105, gain: 2.0, q: 0.7 }, [
    [20, 1.9958718268450384],
    [105, 0.9999999999992859],
    [1000, 0.0006931946745789644],
  ]],
  ['HSC 8000 -3.0 q0.7', { type: 'HSC', fc: 8000, gain: -3.0, q: 0.7 }, [
    [1000, -0.001300311154891513],
    [8000, -1.4999999999999996],
    [20000, -2.9967799878692993],
  ]],
];

console.log('magnitudeDb vs Python reference (tol 1e-6 dB)');
for (const [label, band, points] of MAG_CASES) {
  for (const [f, expected] of points) {
    near(`${label} @ ${f} Hz`, magnitudeDb(band, f), expected, TOL_DB);
  }
}

// ---- axis mapping ---------------------------------------------------------
console.log('axis mapping');
// xlog(1000, 1000) from build_mocks.py = 566.3233347786729.
// NOTE: SPEC.md acceptance item 3 says "1 kHz at 60.2 %"; the reference mapping
// puts it at 56.63 %. The Python reference wins — dsp.js agrees with it.
near('freqToX(1000, 1000)', freqToX(1000, 1000), 566.3233347786729, 1e-9);
near('freqToX(20, 1000)', freqToX(20, 1000), 0, 1e-12);
near('freqToX(20000, 1000)', freqToX(20000, 1000), 1000, 1e-9);
near('freqToX(105, 1000)', freqToX(105, 1000), 240.05310113531897, 1e-9);
near('freqToX(3100, 1000)', freqToX(3100, 1000), 730.1105660567639, 1e-9);

for (const w of [800, 1000, 1440]) {
  for (const f of [20, 105, 440, 1000, 3100, 8000, 20000]) {
    near(`round-trip ${f} Hz @ w=${w}`, xToFreq(freqToX(f, w), w), f, 1e-9);
  }
}

// ---- bandFromMarks --------------------------------------------------------
console.log('bandFromMarks');
{
  const b = bandFromMarks({ start: 2500, top: 3100, end: 3750, kind: 'peak' });
  eq('fc', b.fc, 3100);
  eq('gain', b.gain, -3);
  eq('q (3100/1250 = 2.48 → 2.5)', b.q, 2.5);
  eq('type', b.type, 'PK');
}

// ---- formatting + preamp --------------------------------------------------
console.log('formatting and preamp');
eq('fmtHz(3100)', fmtHz(3100), '3 100'); // thin space U+2009
eq('fmtK(2500)', fmtK(2500), '2.5k');
eq('fmtK(20000)', fmtK(20000), '20k');
eq('autoPreamp([+2, -4.5])', autoPreamp([
  { fc: 105, gain: 2, q: 0.7, type: 'LSC', enabled: true },
  { fc: 3100, gain: -4.5, q: 2.6, type: 'PK', enabled: true },
]), -2);

console.log(`\n${checks - failures}/${checks} checks passed`);
if (failures) {
  console.error(`${failures} failing check(s)`);
  process.exit(1);
}
