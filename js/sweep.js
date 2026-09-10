// SweepStrip — the log-frequency tape with a needle.
// Ported from design/build_mocks.py `tape_svg` with the "Quiet" m_st() style.
// All colours are CSS custom properties, so the theme toggle repaints the tape
// without any JS redraw.

import { MAJOR_TICKS, MINOR_TICKS, freqToX, xToFreq, clampFreq, fmtK } from './dsp.js';

const NS = 'http://www.w3.org/2000/svg';

// Geometry from the mock: base = h - 24, minor ticks 8 px, major 16 px,
// labels 11 px sitting at base + 15, needle from y 6 down to base + 2.
const BASE_INSET = 24;
const MINOR_H = 8;
const MAJOR_H = 16;
const LABEL_DY = 15;
const NEEDLE_TOP = 6;
const NEEDLE_OVERSHOOT = 2;

function el(name, attrs) {
  const n = document.createElementNS(NS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}

// 20 hugs the left edge, 20k hugs the right edge, everything else is centred.
function anchorFor(f) {
  if (f === MAJOR_TICKS[0]) return ['start', 4];
  if (f === MAJOR_TICKS[MAJOR_TICKS.length - 1]) return ['end', -4];
  return ['middle', 0];
}

export class SweepStrip {
  /**
   * @param {SVGSVGElement} svg   existing <svg>; needs display:block and a CSS height
   * @param {{onFreq?:(hz:number)=>void, onPointerDown?:()=>void}} handlers
   */
  constructor(svg, handlers = {}) {
    this.svg = svg;
    this.onFreq = handlers.onFreq || (() => {});
    this.onPointerDown = handlers.onPointerDown || (() => {});

    this.freq = 1000;
    this.w = 0;
    this.h = 0;
    this.pointerId = null;

    svg.style.cursor = 'ew-resize';
    svg.style.touchAction = 'none'; // keep pointermove flowing during a drag

    // Two layers: ticks are rebuilt on resize only, the needle moves every frame.
    this.ticks = el('g', {});
    this.needle = el('line', {
      x1: 0, y1: NEEDLE_TOP, x2: 0, y2: NEEDLE_TOP,
      stroke: 'var(--ink)', 'stroke-width': '1.5',
    });
    svg.appendChild(this.ticks);
    svg.appendChild(this.needle);

    this._onDown = this._onDown.bind(this);
    this._onMove = this._onMove.bind(this);
    this._onUp = this._onUp.bind(this);
    svg.addEventListener('pointerdown', this._onDown);
    svg.addEventListener('pointermove', this._onMove);
    svg.addEventListener('pointerup', this._onUp);
    svg.addEventListener('pointercancel', this._onUp);

    this.ro = new ResizeObserver(() => this._measure());
    this.ro.observe(svg);
    this._measure();
  }

  // --- sizing ---------------------------------------------------------------

  _measure() {
    const r = this.svg.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width));
    const h = Math.max(1, Math.round(r.height));
    if (w === this.w && h === this.h) return;
    this.w = w;
    this.h = h;
    this.svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    this.svg.setAttribute('preserveAspectRatio', 'none');
    this._drawTicks();
    this.update(this.freq);
  }

  _drawTicks() {
    const { w, h } = this;
    const base = h - BASE_INSET;
    const g = this.ticks;
    while (g.firstChild) g.removeChild(g.firstChild);

    for (const f of MINOR_TICKS) {
      const x = freqToX(f, w).toFixed(1);
      g.appendChild(el('line', {
        x1: x, y1: base - MINOR_H, x2: x, y2: base,
        stroke: 'var(--hair2)', 'stroke-width': '1',
      }));
    }

    for (const f of MAJOR_TICKS) {
      const x = freqToX(f, w);
      g.appendChild(el('line', {
        x1: x.toFixed(1), y1: base - MAJOR_H, x2: x.toFixed(1), y2: base,
        stroke: 'var(--faint)', 'stroke-width': '1.5',
      }));
      const [anchor, dx] = anchorFor(f);
      const t = el('text', {
        x: (x + dx).toFixed(1), y: base + LABEL_DY,
        'text-anchor': anchor,
        'font-family': 'var(--sans)', 'font-size': '11.5',
        fill: 'var(--mute)',
      });
      t.textContent = fmtK(f);
      g.appendChild(t);
    }

    this.needle.setAttribute('y2', base + NEEDLE_OVERSHOOT);
  }

  // --- public ---------------------------------------------------------------

  /** Move the needle. Cheap: two attribute writes, no rebuild. */
  update(hz) {
    this.freq = clampFreq(hz);
    const x = freqToX(this.freq, this.w).toFixed(1);
    this.needle.setAttribute('x1', x);
    this.needle.setAttribute('x2', x);
  }

  destroy() {
    this.ro.disconnect();
    this.svg.removeEventListener('pointerdown', this._onDown);
    this.svg.removeEventListener('pointermove', this._onMove);
    this.svg.removeEventListener('pointerup', this._onUp);
    this.svg.removeEventListener('pointercancel', this._onUp);
  }

  // --- pointer --------------------------------------------------------------

  _freqAt(e) {
    const r = this.svg.getBoundingClientRect();
    return clampFreq(xToFreq(e.clientX - r.left, r.width || this.w));
  }

  _onDown(e) {
    if (e.button != null && e.button !== 0) return;
    e.preventDefault();
    this.pointerId = e.pointerId;
    try { this.svg.setPointerCapture(e.pointerId); } catch { /* capture unsupported */ }
    const hz = this._freqAt(e);
    this.onPointerDown();          // app starts the tone and latches
    this.onFreq(hz);
  }

  _onMove(e) {
    if (this.pointerId === null || e.pointerId !== this.pointerId) return;
    this.onFreq(this._freqAt(e));
  }

  _onUp(e) {
    if (this.pointerId === null || e.pointerId !== this.pointerId) return;
    this.pointerId = null;
    try { this.svg.releasePointerCapture(e.pointerId); } catch { /* already released */ }
    // Nothing else: the tone keeps playing after the drag.
  }
}
