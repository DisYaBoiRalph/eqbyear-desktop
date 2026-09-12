// Web Audio engine. Nothing is created until start() runs from a user gesture.
// Chain: osc -> toneGain -> preampGain -> biquad[0..7] -> levelGain -> ceiling
//        -> clipper (hard limit at the ceiling) -> analyser -> destination

const BANDS = 8;
const RAMP = 0.015;      // 15 ms play/stop fade
const GLIDE = 0.008;     // frequency glide time constant
const SMOOTH = 0.01;     // level / filter parameter smoothing
const CEILING = 0.5;     // fixed -6 dBFS output ceiling

const TYPE_MAP = { PK: 'peaking', LSC: 'lowshelf', HSC: 'highshelf' };

const dbToGain = (db) => Math.pow(10, db / 20);

export class AudioEngine {
  constructor() {
    this.state = 'idle';      // 'idle' until start() resolves, then 'running'
    this.ctx = null;
    this.analyser = null;
    this._buf = null;
    // Desired settings kept while idle so start() can apply them.
    this._freq = 1000;
    this._levelDb = -18;
    this._playing = false;
  }

  // Build the graph. Must be called from a user gesture.
  async start() {
    if (this.ctx) {
      if (this.ctx.state === 'suspended') await this.ctx.resume();
      this.state = 'running';
      return;
    }
    const Ctor = window.AudioContext || window.webkitAudioContext;
    if (!Ctor) return;
    const ctx = new Ctor();
    const now = ctx.currentTime;

    this.osc = ctx.createOscillator();
    this.osc.type = 'sine';
    this.osc.frequency.setValueAtTime(this._freq, now);

    this.toneGain = ctx.createGain();
    this.toneGain.gain.setValueAtTime(0, now);

    this.preampGain = ctx.createGain();
    this.preampGain.gain.setValueAtTime(1, now);

    // Eight filters live in the chain for the life of the engine; unused ones
    // sit flat (peaking, 0 dB) so the node graph never has to be rebuilt.
    this.biquads = [];
    for (let i = 0; i < BANDS; i++) {
      const bq = ctx.createBiquadFilter();
      bq.type = 'peaking';
      bq.frequency.setValueAtTime(1000, now);
      bq.Q.setValueAtTime(1, now);
      bq.gain.setValueAtTime(0, now);
      this.biquads.push(bq);
    }

    this.levelGain = ctx.createGain();
    this.levelGain.gain.setValueAtTime(dbToGain(this._levelDb), now);

    this.ceiling = ctx.createGain();
    this.ceiling.gain.setValueAtTime(CEILING, now);

    // Hard clipper: identity up to +/- CEILING, flat beyond. A WaveShaper clamps
    // inputs outside [-1, 1] to the curve's end points, so no boost stacking or
    // manual preamp can push the output past the ceiling. Unlike a compressor
    // it adds no makeup gain, so quiet levels stay exactly as set.
    this.clipper = ctx.createWaveShaper();
    const N = 4097;
    const curve = new Float32Array(N);
    for (let i = 0; i < N; i++) {
      const x = (i / (N - 1)) * 2 - 1;
      curve[i] = Math.max(-CEILING, Math.min(CEILING, x));
    }
    this.clipper.curve = curve;
    this.clipper.oversample = 'none';

    this.analyser = ctx.createAnalyser();
    this.analyser.fftSize = 2048;
    this._buf = new Float32Array(this.analyser.fftSize);

    this.osc.connect(this.toneGain).connect(this.preampGain);
    let node = this.preampGain;
    for (const bq of this.biquads) node = node.connect(bq);
    node.connect(this.levelGain).connect(this.ceiling)
      .connect(this.clipper).connect(this.analyser).connect(ctx.destination);

    this.osc.start();
    this.ctx = ctx;
    if (ctx.state === 'suspended') await ctx.resume();
    this.state = 'running';
    if (this._playing) this.play();
  }

  setFrequency(hz) {
    this._freq = hz;
    if (this.state !== 'running') return;
    this.osc.frequency.setTargetAtTime(hz, this.ctx.currentTime, GLIDE);
  }

  play() {
    this._playing = true;
    this._fade(1);
  }

  stop() {
    this._playing = false;
    this._fade(0);
  }

  // Linear fade of the tone gain, cancelling anything already scheduled so
  // repeated play/stop calls never step the value and click.
  _fade(target) {
    if (this.state !== 'running') return;
    const g = this.toneGain.gain;
    const now = this.ctx.currentTime;
    g.cancelScheduledValues(now);
    g.setValueAtTime(g.value, now);
    g.linearRampToValueAtTime(target, now + RAMP);
  }

  setLevel(db) {
    this._levelDb = db;
    if (this.state !== 'running') return;
    this.levelGain.gain.setTargetAtTime(dbToGain(db), this.ctx.currentTime, SMOOTH);
  }

  // bands: up to 8 {type, fc, gain, q, enabled}. Filters beyond the list, and
  // disabled ones, are set flat. eqOn === false flattens everything and drops
  // the preamp to unity. Preamp sits before the biquads so boosts cannot push
  // the signal past the ceiling.
  setBands(bands, eqOn = true, preampDb = 0) {
    if (this.state !== 'running') return;
    const now = this.ctx.currentTime;
    const list = Array.isArray(bands) ? bands : [];
    this.preampGain.gain.setTargetAtTime(eqOn ? dbToGain(preampDb) : 1, now, SMOOTH);
    for (let i = 0; i < BANDS; i++) {
      const bq = this.biquads[i];
      const b = list[i];
      const live = eqOn && b && b.enabled !== false;
      if (live) {
        // Web Audio's peaking Q is RBJ Q, so fc/Q/gain pass through unchanged.
        // For shelves Web Audio ignores Q while the graph draws RBJ
        // shelf-with-Q, so shelf curves can differ slightly from the plot.
        bq.type = TYPE_MAP[b.type] || 'peaking';
        bq.frequency.setTargetAtTime(b.fc, now, SMOOTH);
        bq.Q.setTargetAtTime(b.q, now, SMOOTH);
        bq.gain.setTargetAtTime(b.gain, now, SMOOTH);
      } else {
        bq.type = 'peaking';
        bq.gain.setTargetAtTime(0, now, SMOOTH);
      }
    }
  }

  // RMS of the time-domain buffer, in dBFS. -Infinity for digital silence.
  analyserDb() {
    if (this.state !== 'running') return -Infinity;
    this.analyser.getFloatTimeDomainData(this._buf);
    let sum = 0;
    for (let i = 0; i < this._buf.length; i++) sum += this._buf[i] * this._buf[i];
    const rms = Math.sqrt(sum / this._buf.length);
    return rms > 0 ? 20 * Math.log10(rms) : -Infinity;
  }
}
