# Instrumented DIY Equatorial Tracker — Draft Design Notes

> **Status: DRAFT — not committed.** This captures the reasoning and the numbers from the
> design discussion of 2026-09-27 so it can be picked up later. Architecture choices below are
> *working assumptions*, not decisions. See "Before committing" at the end.

---

## 1. Context — how we got here

Goal: a single-axis (RA-only) equatorial star tracker for a Micro Four Thirds camera, built
mostly from 3D-printed parts, good enough for 2–5 minute subs at 150 mm (headroom to 300 mm),
at 46° N.

The project started from an **open-loop premise**: level the base precisely with an
accelerometer, set altitude to the known latitude, aim north. That premise was abandoned for
two independent reasons:

1. **Gravity-referenced tilt sensing cannot deliver useful polar alignment.**
   - 1 arcsec of tilt = **4.85 µg**. Arcsecond tilt sensing means µg accelerometry.
   - Cheap MEMS drifts ~**31 arcsec/°C** (ADXL355, ±0.15 mg/°C). The MPU-6050 on the GY-87 is
     ~1000× worse still (±50/80 mg zero-g offset ≈ 3–5 arcmin).
   - Measuring a **46° angle** rather than a null makes **scale-factor error** dominant:
     `dφ = ε · cot φ`, so 1 % sensitivity error → **~29 arcmin**. Offset calibration doesn't
     touch this. (Precision inclinometers avoid it by working at null.)
   - Even with a perfect sensor: gravity defines the **astronomical** latitude, while GPS gives
     the **geodetic** one. The difference (plumb-line deflection) is 1–10 arcsec typically but
     **30–100 arcsec in mountainous terrain** — which is where we observe.
   - Refraction adds ~56 arcsec at 46° latitude (apparent pole above true pole), varying with
     temperature and pressure.

2. **Plate solving measures the polar axis directly**, and the camera↔axis offset — the thing
   that seemed like the hard problem — cancels out entirely. See §2.

**Consequence:** the mount became a *closed-loop, instrumented* system, and diagnosability
became a primary requirement rather than an afterthought.

---

## 2. Why the camera↔axis offset doesn't matter

Rotate the RA axis and every star undergoes a rigid rotation on the celestial sphere. **The
axis of that rotation is the mount's polar axis, by definition.** A fixed camera offset is a
constant rigid transform — it shifts every pointing direction identically and therefore cannot
change the axis of rotation between them. It cancels out of the fit.

- **N.I.N.A. "Three Point Polar Alignment"**: plate solve at 3 RA positions → 3 pointing vectors
  on a small circle → fit the circle → **its centre is the polar axis.** The camera offset is
  the circle's *radius*, a fitted nuisance parameter.
- **SharpCap**: plate solving returns full orientation (RA, Dec **and** camera rotation angle),
  so two positions ~90° apart fully determine the rotation, and its axis is the polar axis.

Three consequences, one of which inverts the original assumption:

1. **A large camera offset is wanted, not zero.** Pointing along the axis makes the circle
   degenerate and the fit singular. 10–40° off-axis is well conditioned. Ball-head-on-top is ideal.
2. **Only rigidity during the sequence matters.** Lock the ball head, run the routine, re-aim freely after.
3. **Base levelling barely matters** — a level base only keeps the alt/az adjustments decoupled
   and orthogonal (fewer iterations) and makes the altitude scale read latitude. **±0.5° with a
   €5 bubble is sufficient.** The accelerometer was solving a non-problem.

---

## 3. Target specification

MFT sensor, ~3.3 µm pixels → **4.5 arcsec/px at 150 mm**, 2.3 arcsec/px at 300 mm.
Seeing 1.5–3 arcsec → 150 mm is pixel-limited, not seeing-limited.

**Budget: total tracking error < 4 arcsec per 300 s sub at 150 mm.**

Drift from polar misalignment: `drift = Δ · ω · T`, ω = 7.292e-5 rad/s.

| Term | Allocation | Means |
|---|---|---|
| Polar alignment | < 1 arcsec/300 s | plate solve to ≤ 45 arcsec |
| Drive transmission error | < 2 arcsec residual | cascade loop (raw printed error ~150 arcsec) |
| Motor/microstep ripple | < 1 arcsec | large reduction + encoder inner loop |
| Timebase | < 0.3 arcsec | crystal, **86164.0905 s sidereal day** |
| Flexure / thermal | < 1 arcsec | counterweight + metal load path |

### Reality check on the original plan

| Error source | Realistic magnitude | vs. 4 arcsec budget |
|---|---|---|
| Polar alignment, plate-solved (30 arcsec) | 0.66 arcsec/300 s | ✅ 6× margin |
| Crystal timebase (±50 ppm) | 0.23 arcsec/300 s | ✅ negligible |
| **Solar rate instead of sidereal** (a real bug) | **12 arcsec/300 s** | ❌ 3× over |
| Stepper microstep error (±5 % full step ÷ 105) | ±1.6 arcsec | ⚠️ borderline |
| Bearing play (10 µm ÷ 30 mm spacing) | 69 arcsec | ❌ 17× over |
| **3D-printed cycloidal transmission error** | **~150–500 arcsec p-p** | ❌❌ **40–125× over** |

**The binding constraint is the drive, not the alignment.** Alignment has 6× margin and is
essentially free. This is why the accelerometer effort was misdirected.

Printed-drive estimate: ~±100 µm tooth/pin position error on a tuned printer; on a 40 mm pitch
radius that's 2.5e-3 rad = **515 arcsec**, load-shared across ~10 pins → ~150 arcsec. A bought
bronze worm is 30–60 arcsec; a good commercial mount 5–15 arcsec.

> **Recurring lesson, three times over:** resolution ≠ accuracy. 20-bit accelerometer,
> 1 arcsec/microstep, 14-bit encoder — none of these tell you where anything actually is.

---

## 4. Working architecture

### 4.1 Cascaded control

```
Pi  ── guide camera, 0.2–0.5 Hz ──►  OUTER loop (sky-referenced, absolute)
                                     removes: polar residual, flexure,
                                     refraction, encoder bias
                 │ rate offset (ppm) + pulse-guide, over serial
                 ▼
ESP32 ── output encoder, ~1 kHz ──►  INNER loop (shaft-referenced, relative)
                                     removes: pin-pass ripple, PE,
                                     microstep ripple, stiction events
       ── input encoder,  ~1 kHz ──►  motor delivery telemetry only
```

Structurally identical to cascade temperature control — fast jacket loop inside a slow reactor
loop. The inner loop rejects fast disturbances; the outer loop supplies the true setpoint and
removes the inner sensor's bias.

**Why this matters:** correcting *during* a sub means the main camera is busy collecting
photons and cannot be the feedback sensor. In-sub correction therefore requires a second sensor
— guide camera, encoder, or both.

**The inner loop is what makes a printed cycloidal drive viable.** Pin-pass error is far too
fast for a 2 s camera loop but essentially DC to a 1 kHz encoder loop. (Note: an earlier
argument that "cycloidal error is too fast to guide out" is true only for a camera-only loop.)

### 4.2 Drivetrain — working proposal

GT2 belt **16T→48T = 3:1**, then single-stage cycloidal **35 lobes / 36 pins = 35:1**.
**Total 105:1.**

| Quantity | Value |
|---|---|
| Output rate | 1 rev / 86164.0905 s |
| Motor (0.9°, 400 steps) at 1/16 µstep | 7.80 µsteps/s |
| Output resolution | 1.93 arcsec/µstep (0.96 at 1/32) |
| Motor revolution period | 820.6 s (13.7 min) |
| Cycloidal pin-pass period | 68 s |
| Belt tooth-pass period | 51 s |
| Motor detent ripple (100 pole pairs) | 8.2 s |

All error periods ≥ 8.2 s — slow relative to a 1 kHz inner loop. **The 8.2 s detent ripple is
the term a camera-only loop could not have corrected**, which is what justifies the cascade.

Torque: 105:1 from a NEMA14 gives ~40 Nm — hugely overspecified. **Run low current
deliberately**: less heat → less thermal drift.

**Make the drive a bolt-on module** with a defined interface to the polar-axis housing, so a
bought worm can be swapped in as a reference drive without redesigning the mount.

### 4.3 Mechanical stack

| Layer | Design | Build |
|---|---|---|
| 0 Tripod / coarse level | 3/8" screw, 3× M6 opposed levelling screws, bullseye bubble. ±0.5° suffices | printed |
| 1 Azimuth fine adjust | ±10° travel, two **opposed tangential screws** on ≥100 mm lever arm; radial clamp lock | printed + bought screws |
| 2 Altitude fine adjust | wedge printed at 46° nominal, hinge on steel dowel, opposed screws on ~120 mm arm. **Main bending load path — reinforce** | printed + Al angle |
| 3 Polar axis | **BUY MACHINED.** ⌀12–15 mm steel shaft, preloaded angular-contact or tapered pair, ≥80 mm spacing, machined Al housing | bought/machined |
| 4 Cycloidal drive | printed discs (2× at 180°), bought ground dowel pins, **machined eccentric** | hybrid |
| 5 Camera + counterweight | 3/8" ball-head boss + counterweight arm opposite | printed |

**Adjuster resolution:** 30 arcsec on a 100 mm arm = **14.5 µm** = 1/48 turn of M4×0.7. Use
opposed screws (always in compression), never a screw against a spring — springs vary and
printed parts relax. A differential screw (M6×1.0 in M5×0.8 → 0.2 mm/turn) makes it a
comfortable 26° of knob. Verify **locking doesn't shift the axis** — that's where cheap mounts
lose arcminutes.

**Bearings:** axis tilt ≈ radial play ÷ bearing spacing. 6800-series has 3–18 µm clearance:
over 30 mm spacing = 69 arcsec, over 120 mm = 17 arcsec. A **preloaded pair** drives play toward
zero. Route preload through a **metal** path — printed parts creep and lose it in weeks.

**Layout constraint:** the output encoder magnet needs a free shaft end → camera boss at one
end, encoder at the other, drive in between.

**Buy-machined priority:** (1) polar shaft + bearing housing, (2) cycloidal eccentric. These
two dominate achievable accuracy. Everything else prints.

**Materials reality:** printed PLA realises ~2.2 GPa vs aluminium's 70 GPa — **~30× more
compliant** — plus room-temperature creep under sustained load, plus CTE ~70 µm/(m·K) vs 23 (Al)
and 12 (steel). Keep printed parts **out of the load path and out of the axis definition**.

### 4.4 Why the counterweight is not optional

A printed cycloidal drive has real torsional compliance. An unbalanced camera applies a
*varying* torque as RA rotates → windup that changes with angle, indistinguishable from PE but
not periodic. Balancing also keeps flexure independent of RA angle and lets motor current drop.
Keep a **small deliberate residual imbalance** in one direction so the drive flank stays loaded
and backlash never reverses during guide corrections.

### 4.5 Sensing

| Sensor | Placement | Purpose |
|---|---|---|
| AS5048A + diametric magnet | motor shaft | delivered rate, missed steps, microstep ripple (÷105 → ~1.7 arcsec equiv.) |
| AS5048A + diametric magnet | polar shaft free end | inner-loop feedback; INL calibrated against sky |
| 2× DS18B20 | wedge, drive housing | thermal drift regression |
| TMC2209/5160 UART | — | motor current, StallGuard → stiction/binding |

**Encoder accuracy reality:** 14-bit = 79 arcsec/count *resolution*, but ±0.05–0.5° absolute,
dominated by magnet centring. Survivable because (a) input-shaft errors divide by 105, and
(b) INL is a smooth, repeatable low-harmonic function of shaft angle, so it calibrates out
against the sky — residual ~10–20 arcsec. That residual is **still above budget**, which is
exactly why the camera must remain the outer loop.

> `output_encoder − input_encoder/105` **is the transmission error** — measured continuously,
> indoors, in daylight, no sky needed. Single most valuable diagnostic in the build.

### 4.6 Software stack

- **ESP32** — hardware-timer/MCPWM step generation, 1 kHz SPI encoder sampling, inner PI loop,
  timestamped telemetry. Crystal timebase (±50 ppm = 0.23 arcsec/300 s; no TCXO needed).
- **Pi** — guide camera, plate solving (ASTAP / astrometry.net), main camera via gphoto2,
  outer loop. **Emulate the LX200 protocol** on the ESP32 serial link so PHD2 works unmodified.
- **MATLAB** — offline analysis and dashboard.

> **Timestamping is what DIY telemetry gets wrong.** Camera exposures, encoder samples and motor
> commands must share one clock. Discipline the ESP32 against the Pi and log a periodic sync
> marker in the telemetry stream.

---

## 5. MATLAB toolchain

Available (R2025b, verified): Signal Processing (**`plomb`** — essential, frames are irregularly
sampled), Curve Fitting, Image Processing (`regionprops` WeightedCentroid), Statistics,
Optimization, Computer Vision, Simulink.
**No Control System Toolbox** — design the inner loop empirically or in Simulink.
**No Aerospace Toolbox** — coordinate transforms stay hand-rolled (already started).

### Reuse
- **`StarFinder.m`** — the threshold/mask logic is the seed of the centroid detector. Replace the
  `img > 210` mask with connected components + subpixel fit (~1/10 px ≈ 0.45 arcsec).
- **`Basic_Visualizations.m`** — the `R_3D_x/y/z` rotation-matrix lambdas and the Rodrigues
  `R_3D_u` construction carry directly over to RA/Dec↔Alt/Az and to the small-circle fit.

### New functions (camelCase)
| File | Role |
|---|---|
| `detectStars.m` | threshold + `regionprops` + subpixel weighted centroid |
| `fitStarCentroid.m` | 2-D Gaussian PSF fit for the precision path |
| `trackStarDrift.m` | track stars across a sub sequence → x(t), y(t) in arcsec |
| `estimatePeriodicError.m` | detrend, `plomb`, harmonic ID vs. known mechanism periods |
| `allanDeviation.m` | Allan deviation → optimal guide cadence |
| `calibrateEncoderInl.m` | fit low harmonics of encoder vs. sky truth → correction table |
| `computeTransmissionError.m` | `out − in/105`, with ratio and phase estimation |
| `readTelemetryLog.m` | parse ESP32 telemetry, align to frame timestamps |
| `fitPolarAxis.m` | small-circle fit through ≥3 plate-solved pointings → axis direction |

### New scripts (PascalCase_snake_case)
`DriveTestRig_Analysis.m`, `PeriodicError_SkyMeasurement.m`, `EncoderCalibration_Sky.m`,
`ThermalDrift_Regression.m`, `TrackerDashboard.mlapp`

All physical quantities in SI internally (rad, rad/s, m, s); convert to arcsec only for display.

### What the dashboard can estimate

| Quantity | From |
|---|---|
| PE curve + harmonic decomposition | camera or encoder diff, `plomb` |
| Effective delivered rate (ppm error) | input encoder vs. commanded |
| Missed steps / step-loss events | input encoder vs. commanded (indoors) |
| Transmission error | `out − in/105` (indoors) |
| Backlash / lost motion | reverse drive, encoder diff (indoors) |
| Stiction & binding | motor current vs. angle |
| Optimal guide cadence | Allan deviation of residual |
| Thermal drift coupling | temps vs. residual, regression |
| Polar alignment residual | camera drift, Dec vs. time |

---

## 6. Staged build — de-risk before committing

**Stage 0 — Analysis chain first, no hardware.** Build and validate `detectStars` /
`fitStarCentroid` / `trackStarDrift` against existing images. Measure actual centroiding
precision. Costs nothing, de-risks everything downstream.

> ⚠️ **Critical gotcha:** `DSS_Outputs\*.jpg` are **stacked** files. Stacking aligns out exactly
> the drift we want to measure, and 8-bit JPEG destroys photometric linearity. Stage 0 can
> validate the centroider on them, but **all PE measurement must use un-stacked, un-aligned
> individual subs in RAW/FITS.**

**Stage 1 — Bench drive rig. THE DECISION GATE.** Cycloidal + both encoders + ESP32; no mount,
no sky. Measure transmission error indoors and iterate print parameters (discs printed face-down
in XY, fine nozzle, per-axis shrinkage compensation). **This answers the riskiest question in the
project — whether a printed cycloidal can be controlled to spec — before any mount is built.**
If it fails, the bolt-on drive interface means falling back to a bought worm costs a print,
not a redesign.

**Stage 2 — Mount mechanics.** Base, azimuth, altitude, polar axis. Verify by drift test.

**Stage 3 — Open-loop tracking + sky PE characterisation.** Establishes the uncorrected baseline.

**Stage 4 — Inner encoder loop.** Re-measure; expect the 8.2 / 51 / 68 s lines to collapse.

**Stage 5 — Guide camera outer loop + plate-solve polar alignment.**

**Stage 6 — Dashboard.**

---

## 7. Verification plan

| Stage | Test | Pass criterion |
|---|---|---|
| 0 | centroid repeatability on a static star field | ≤ 0.2 px RMS |
| 1 | `computeTransmissionError` over ≥ 3 output revs, bench | spectral lines match predicted 51/68/820 s |
| 1 | backlash: reverse drive, measure lost motion | quantified and documented |
| 2 | drift test, star near Dec 0° on meridian | polar residual ≤ 45 arcsec after plate solve |
| 3 | `estimatePeriodicError` over ≥ 2 full drive periods (≥ 30 min of 2–5 s subs) | PE curve + harmonic attribution |
| 3 | delivered rate vs. commanded, input encoder | < 50 ppm; **confirm sidereal not solar** |
| 4 | repeat Stage 3, inner loop closed | fast lines suppressed; residual < 10 arcsec |
| 5 | 300 s sub at 150 mm, guided | star FWHM elongation < 1 px |
| all | flexure: hang known mass, measure image shift | quantified, ideally < 2 arcsec |
| all | thermal: `ThermalDrift_Regression` over a session | drift coefficient identified |

Run MATLAB via the MATLAB MCP server (`run_matlab_file`, `check_matlab_code`). Do a dimensional
analysis after any drivetrain-ratio or error-budget model change.

---

## 8. Before committing — what to learn first

Nothing here is decided. The two cheapest, highest-information things to do first, both of which
need **no new hardware**:

1. **Try plate-solve polar alignment on the current setup.** SharpCap or N.I.N.A. with the
   existing camera. This validates the whole premise of §2 and teaches what alignment accuracy
   actually feels like before designing adjusters for it.
2. **Do Stage 0.** Build the centroiding chain on existing images. It's the measurement
   instrument for everything else, and it's pure MATLAB.

Topics worth reading up on, roughly in order of leverage:

| Topic | Why it matters here |
|---|---|
| Plate-solve polar alignment (SharpCap PA, N.I.N.A. TPPA) | the premise of the whole redesign |
| Autoguiding & PHD2 (guide cadence, RA-only guiding) | the outer loop; determines if a guide camera is needed |
| Periodic error & PEC in mounts | what a PE curve looks like and how it's normally handled |
| Cycloidal drive kinematics | ratio formula, pin/lobe counts, sensitivity to eccentricity error |
| Cascaded control / bandwidth separation | why inner+outer works; needed to tune the loop |
| Magnetic encoder INL and calibration | whether ±0.05–0.5° really calibrates down to 10–20 arcsec |
| Stepper microstepping accuracy; TMC drivers | why microstep ≠ position, StealthChop smoothness |
| Star centroiding / PSF fitting | precision limit of the measurement instrument |
| Bearing preload & axis error motion | the 69-vs-17 arcsec difference in §4.3 |
| 3D print dimensional accuracy, anisotropy, creep | the ±100 µm assumption behind the 150 arcsec estimate |

### Open items
- Guide camera selection (cheap mono + finder scope vs. repurposed sensor).
- Whether to add a declination axis in v2 — needed above ~300 mm. At 150 mm, RA-only guiding
  with 45 arcsec polar alignment gives ~1 arcsec dec drift per sub; session-scale shift is
  removed by frame registration.
- Inner-loop gain design: empirical, or a Simulink model of drive compliance.
- Whether printed cycloidal survives Stage 1 at all — the single biggest unknown.

### Decisions log (working assumptions, 2026-09-27)
| Choice | Selected | Status |
|---|---|---|
| Feedback | Cascade: encoders + guide camera | assumption |
| Drive | Printed cycloidal | **highest-risk assumption** — Stage 1 gate |
| Stack | ESP32 motion / Pi imaging / MATLAB offline | assumption |
| Manufacturing | Printer + bought hardware, few machined parts | assumption |
| Target | 150 mm now, headroom to 300 mm, 2–5 min subs | assumption |
