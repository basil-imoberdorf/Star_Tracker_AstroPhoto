# Learning Roadmap — Instrumented Star Tracker

> Companion to `TrackerDesign_DraftPlan.md`. Purpose: orient the learning process before
> committing to any design. **Part 1 (Software) first, Part 2 (Hardware) second.**
>
> Approach: **write it yourself first, swap in the optimised open-source tool later.** Each topic
> names both — what to build to understand it, and what you'd eventually use in production. The
> point of writing it yourself is not to produce the final code; it is to know what the
> production tool is actually doing and to be able to tell when it lies to you.

**Effort key:** ◔ an evening · ◑ a weekend · ◕ a week or two of evenings · ● a month+
**Conventions:** all code SI internally (rad, s, m); arcsec only at display. Functions camelCase,
scripts PascalCase_snake_case.

---

# PART 1 — SOFTWARE

## S1. Measurement foundation: image → star positions ◕

**Why first:** this is the instrument every other measurement depends on. Until you can measure a
star position and *know your uncertainty*, nothing else in the project is falsifiable.

### S1.1 Image data and linearity ◔
- [ ] RAW vs JPEG vs FITS; what stretching and 8-bit quantisation destroy
- [ ] **Why stacked images are useless here** — stacking aligns out the drift you want to measure
- [ ] Bayer pattern, demosaicing; why you may prefer to work on one raw channel
- [ ] Black level, saturation, bit depth, linearity of the sensor response
- [ ] Reading your MFT raws in MATLAB (`rawread`, Image Processing Toolbox) and FITS (`fitsread`)

### S1.2 Calibration frames ◔
- [ ] Bias, dark, flat — what each removes and why
- [ ] Dark current vs. temperature and exposure
- [ ] **Hot pixels masquerade as stars** — the single most common centroiding failure
- [ ] Bad-pixel maps

### S1.3 Star detection ◑
- [ ] Why a global threshold fails (your current `img > 210`) — vignetting, gradients, moonlight
- [ ] Local background estimation: sigma-clipped median, background mesh
- [ ] Noise model: Poisson (photon) + Gaussian (read) → threshold expressed in σ, not DN
- [ ] Connected components, `regionprops`
- [ ] Rejection: hot pixels, cosmic rays, saturated stars, close doubles, trailed stars

### S1.4 Subpixel centroiding ◑
- [ ] Centre-of-mass / weighted centroid, and its **bias when background isn't removed**
- [ ] 2-D Gaussian PSF fit (`lsqnonlin` / `fit`); Moffat profile for real optics
- [ ] Quadratic peak interpolation as a fast approximation
- [ ] **Precision limits:** roughly FWHM/SNR; the Cramér–Rao bound for centroiding
- [ ] When each method is appropriate (speed vs. precision)

### S1.5 Validating your own instrument ◑
- [ ] **Synthetic star injection**: generate images with known positions, recover them, measure bias and scatter
- [ ] Repeatability on a real static field
- [ ] Reporting uncertainty, not just a number

> ⚠️ Skipping S1.5 is the classic mistake. A centroider you haven't tested against ground truth
> is a random number generator with good manners.

**Build:** `detectStars.m`, `fitStarCentroid.m`, plus a synthetic-image generator for validation.
**Reuse:** `StarFinder.m` (the mask logic is the seed).
**Production equivalents:** SExtractor/SEP, photutils `DAOStarFinder`, `IRAFStarFinder`.

---

## S2. Error analysis and signal processing ◑

**Why here:** this is your existing strength, and it makes S1's output interpretable. Learn it
early so every later measurement lands in a framework you already trust.

### S2.1 Detrending and decomposition ◔
- [ ] Why you remove the linear term first (it *is* the polar misalignment + rate error)
- [ ] Robust fitting so outliers don't drag the trend

### S2.2 Spectral analysis ◑
- [ ] FFT vs **Lomb–Scargle** (`plomb`) — your frames are irregularly sampled (clouds, download time)
- [ ] Windowing, leakage, frequency resolution vs. record length
- [ ] **Attributing peaks to mechanism frequencies** (motor rev, pin-pass, belt tooth-pass)
- [ ] Harmonic families: a distorted periodic error is not one line

### S2.3 Allan deviation ◑
- [ ] Definition, computation, and how to read the log–log slopes
- [ ] Noise identification: white (−1/2), flicker/bias-instability (flat), random walk (+1/2), drift (+1)
- [ ] **Using it to choose guide exposure and correction cadence**
- [ ] Note: this is the same tool that would characterise an accelerometer bias — one method, two uses

### S2.4 What is correctable ◔
- [ ] Loop bandwidth vs. error frequency — why an 8.2 s ripple is invisible to a 2 s camera loop
- [ ] Error budget arithmetic: adding terms in quadrature vs. linearly

**Build:** `estimatePeriodicError.m`, `allanDeviation.m`
**Production equivalents:** AllanTools (Python), PECPrep.

---

## S3. Celestial coordinates and time ◑

**Why:** every astrometric quantity depends on getting this right, and it is unglamorous,
fiddly, and easy to get subtly wrong.

### S3.1 Coordinate systems ◑
- [ ] RA/Dec, hour angle, alt/az, and the transforms between them
- [ ] Equinox and epoch: J2000 vs. of-date; precession, nutation, aberration
- [ ] **Geodetic vs. astronomical latitude** (the plumb-line deflection that killed the accelerometer idea)
- [ ] Unit vectors and rotation matrices as the clean way to do all of it

### S3.2 Time ◔
- [ ] UTC, UT1, TAI, TT; leap seconds
- [ ] Julian Date, Modified JD
- [ ] **Local Sidereal Time** — needed for every alt/az conversion
- [ ] **Sidereal day = 86164.0905 s, not 86400.** Using solar rate costs 12 arcsec per 5-min sub

### S3.3 Refraction ◔
- [ ] The `R ≈ 58.3″ · tan z` approximation and where it breaks down
- [ ] Temperature/pressure dependence
- [ ] True pole vs. refracted pole — which one you should actually align to

**Build:** `raDecToAltAz.m`, `localSiderealTime.m`, `refractionCorrection.m`
**Reuse:** the `R_3D_x/y/z` and Rodrigues lambdas already in `Basic_Visualizations.m`.
**Note:** no Aerospace Toolbox installed → hand-roll these. That's good for learning anyway.
**Production equivalents:** ERFA/SOFA, astropy.coordinates.

---

## S4. Astrometry and plate solving ●

**Why:** the outer loop's sensor. Also the biggest single software topic in the project — be
realistic about scope here.

### S4.1 Projections and WCS ◑
- [ ] Gnomonic (TAN) projection — the standard, and why
- [ ] FITS WCS keywords: CRPIX, CRVAL, CD matrix; what each means geometrically
- [ ] Lens distortion and SIP polynomials — matters at wide field

### S4.2 Star catalogues ◔
- [ ] Tycho-2, Gaia, HYG — coverage, magnitude limits, proper motion
- [ ] Indexing for fast spatial query (k-d tree, HEALPix)

### S4.3 Constrained solving (do this first) ◑
- [ ] Given an *approximate* pointing: project catalogue stars, match nearest neighbours
- [ ] RANSAC for outlier rejection
- [ ] Least-squares fit of the linear WCS, then distortion terms
- [ ] **This is a weekend project and is sufficient for a tracker that roughly knows where it points**

### S4.4 Blind solving (understand, probably don't build) ●
- [ ] The astrometry.net approach: geometric hashing of 4-star "quads"
- [ ] Why quad hash codes are invariant under translation, rotation and scale
- [ ] Index files and the verification step (Bayesian decision, false-positive control)

> **Scope warning:** a full blind solver from scratch is a month-plus project and reimplements
> something excellent that already exists. Build S4.3 to understand the geometry; use ASTAP or
> astrometry.net for S4.4. This is the first natural "stop and use the real tool" checkpoint.

**Build:** `solvePlateConstrained.m`, `matchCatalogStars.m`
**Production equivalents:** astrometry.net (`solve-field`), ASTAP, Astrometry.net index files.

---

## S5. Polar alignment mathematics ◑

**Why:** this is the piece that made the accelerometer unnecessary. It's also surprisingly small
once S3 and S4 exist — satisfying after the slog of S4.

### S5.1 Recovering the rotation axis ◑
- [ ] **Three-point method:** 3 pointing unit vectors lie on a small circle; fit a plane through
      them (SVD); the plane normal **is** the polar axis
- [ ] **Two-orientation method:** if plate solving gives full orientation, `R = R₂ · R₁ᵀ`, then
      extract the axis via Rodrigues or quaternion. More robust; this is SharpCap's approach
- [ ] **Why the camera↔axis offset cancels**: a constant rigid transform cannot change the axis
      of rotation between pointings

### S5.2 Conditioning and error propagation ◑
- [ ] Why a *large* camera offset (10–40°) is wanted — a zero offset makes the fit singular
- [ ] How RA rotation span affects conditioning
- [ ] **Monte Carlo it in MATLAB:** propagate centroid noise → plate solve → axis estimate.
      This tells you the alignment accuracy you can actually expect, before building anything

### S5.3 From axis error to knob turns ◔
- [ ] Decomposing the axis error into altitude and azimuth corrections
- [ ] Coupling when the base isn't level (why levelling matters a little, but only a little)
- [ ] Which pole to target given refraction

**Build:** `fitPolarAxis.m`, `polarAlignMonteCarlo.m`
**Production equivalents:** N.I.N.A. Three Point Polar Alignment, SharpCap Polar Align.

---

## S6. Tracking rates and kinematics ◔

- [ ] Sidereal, solar, lunar, King rate — and when each applies
- [ ] Expressing corrections as ppm rate offsets vs. pulse-guide durations
- [ ] Guide rate conventions (e.g. 0.5× sidereal) and what a "pulse" actually commands
- [ ] Refraction-corrected tracking rate (advanced; skip on first pass)

**Build:** `siderealRate.m`, extend into the motion command layer.

---

## S7. Control theory ◑

**Why:** you need this before writing firmware, or you will write a loop that oscillates and not
know why. **Head start:** cascade control is bread-and-butter process engineering — you likely
already have most of the intuition from jacket/reactor temperature loops.

### S7.1 Fundamentals ◔
- [ ] P, PI, PID; why integral action is essential for tracking a *rate*
- [ ] Discrete-time implementation: sampling, difference equations
- [ ] Anti-windup, bumpless transfer, output saturation

### S7.2 Cascade structure ◑
- [ ] Inner/outer loop roles; the **bandwidth separation rule** (inner ≥ 5–10× outer)
- [ ] Why the inner loop removes the outer sensor's blind spots and vice versa
- [ ] How the outer loop removes the inner sensor's *bias* (encoder INL) — the key trick

### S7.3 System identification ◑
- [ ] Step and frequency response of the drive; estimating compliance and friction
- [ ] Deadtime: the camera loop has enormous delay (exposure + download + solve)
- [ ] Stability margins; why delay eats phase margin

### S7.4 Simulation before firmware ◑
- [ ] Build the loop in **Simulink** (installed) and inject your measured error spectrum
- [ ] Note: **no Control System Toolbox** — tune empirically or via Simulink, not `pidtune`

**Build:** a Simulink model of the cascade with realistic delay and a measured disturbance.

---

## S8. Embedded firmware ●

**Why:** the biggest skill jump from MATLAB. Budget accordingly and be patient with yourself.

### S8.1 C/C++ for embedded ◕
- [ ] Pointers, structs, fixed-width integer types, memory layout
- [ ] No dynamic allocation in real-time paths; why
- [ ] Integer vs. floating-point arithmetic on a microcontroller

### S8.2 ESP32 platform ◕
- [ ] Toolchain: ESP-IDF vs. Arduino core; which to learn
- [ ] FreeRTOS tasks, priorities, queues
- [ ] Interrupts and ISR constraints — what may *not* happen inside one
- [ ] Hardware timers, MCPWM, RMT

### S8.3 Motion generation ◑
- [ ] **Why `delay()` is wrong** — jitter directly becomes tracking error
- [ ] Hardware-timer step generation; constant-rate pulse trains
- [ ] Changing rate smoothly without losing steps

### S8.4 Stepper drivers ◑
- [ ] Microstepping: what it does and **why it isn't accuracy** (~5 % of a full step regardless)
- [ ] Current control, chopper modes; StealthChop vs. SpreadCycle
- [ ] TMC2209/5160 UART register interface, StallGuard

### S8.5 Sensor interfacing ◑
- [ ] SPI and I²C; reading AS5048A-class encoders
- [ ] Sampling rate, aliasing, filtering at source
- [ ] Angle unwrapping and rollover handling

### S8.6 Timekeeping ◔
- [ ] Crystal accuracy and drift; ±50 ppm is fine here, TCXO is not needed
- [ ] Syncing the MCU clock to a host

**Production equivalents:** OnStep, GoTo firmware projects, grbl (for motion-control patterns).

---

## S9. Communication and integration ◕

### S9.1 Serial protocols ◑
- [ ] UART basics; framing, checksums, escaping
- [ ] Binary vs. ASCII/JSON — throughput vs. debuggability
- [ ] Designing a command set (or **emulating LX200**, so PHD2 works unmodified)

### S9.2 Host side ◔
- [ ] MATLAB `serialport`: callbacks, buffering, avoiding dropped data
- [ ] Robustness: reconnection, timeouts, malformed frames

### S9.3 Time synchronisation across devices ◑
- [ ] **The thing DIY telemetry gets wrong.** Camera exposures, encoder samples and motor
      commands must share one clock
- [ ] Sync markers, offset/drift estimation, post-hoc alignment of logs

### S9.4 The astro software ecosystem ◔
- [ ] INDI vs. ASCOM — what a "driver" means, what interfaces a mount must expose
- [ ] PHD2: guiding algorithms, calibration, what it expects from a mount
- [ ] Camera control: gphoto2 / libgphoto2 for the MFT body

---

## S10. Data management and dashboard ◑

- [ ] Data model: what to log, at what rate, in what format (long vs. wide, one file per session)
- [ ] Session metadata: config, temperatures, optics, so a result is reproducible months later
- [ ] MATLAB **App Designer**: live plotting, ring buffers, keeping the UI responsive
- [ ] **Version control (git)** — this folder isn't a repo yet; worth fixing early
- [ ] Separating acquisition, storage and analysis so each can change independently

**Build:** `readTelemetryLog.m`, `TrackerDashboard.mlapp`

---

# PART 2 — HARDWARE

> Start once S1–S5 are working, i.e. once you can **measure** what hardware does. Building
> hardware you cannot measure is how this project fails.

## H1. Mechanics fundamentals ◑
- [ ] Stiffness and deflection: cantilever bending, second moment of area, why section depth wins
- [ ] Material properties: Young's modulus, CTE, **creep**, glass transition
- [ ] PLA ~2.2 GPa vs. aluminium 70 GPa — the 30× compliance gap and what it implies
- [ ] Tolerance stack-up; basic GD&T vocabulary (flatness, perpendicularity, runout)
- [ ] Kinematic vs. elastic-averaging mounting principles
- [ ] Balance: why a counterweight is a stiffness and control feature, not just convenience

## H2. Bearings and axis design ◑
- [ ] Types: deep groove, angular contact, tapered roller, thin-section, crossed roller
- [ ] **Preload** — why it matters more than bearing quality, how to apply and retain it
- [ ] Error motion: radial/axial runout, tilt; **axis tilt ≈ play ÷ bearing spacing**
- [ ] Shaft and housing fits (h6/H7), press fits, retention
- [ ] Why preload must be carried by a metal path (printed parts creep and lose it)

## H3. Drivetrain ◕
- [ ] Gear fundamentals: ratio, backlash, **transmission error**, efficiency
- [ ] **Cycloidal drives**: kinematics, pin/lobe counts, ratio formula, sensitivity to eccentric error
- [ ] Worm drives: why mounts use them, and the mechanisms behind periodic error
- [ ] Belt drives: tooth-pass error, tension, pulley runout
- [ ] Friction/roller drives: no tooth error, but slip
- [ ] Backlash management; **why unidirectional tracking with a load bias mostly sidesteps it**
- [ ] Torsional compliance and windup under varying load

## H4. Motors and actuation ◑
- [ ] Stepper fundamentals: full/half/micro stepping, torque–angle curve, detent torque
- [ ] **Why microstepping is resolution, not accuracy**
- [ ] Driver selection and tuning; smoothness at very low speed
- [ ] **Stick-slip at 4.2 input rev/hour** — a real risk at tracker speeds
- [ ] Thermal: motor heat → structure heat → drift; why running low current is a feature
- [ ] Alternatives: DC servo + encoder, direct drive

## H5. Sensors and metrology ◑
- [ ] Magnetic encoders: operating principle, **INL**, magnet centring, shaft runout
- [ ] Calibrating a sensor against a better reference (here: the sky)
- [ ] Optical and tape encoders — what the expensive option buys
- [ ] Temperature sensor placement and self-heating
- [ ] **Resolution vs. accuracy vs. repeatability** — the distinction this project keeps re-learning
- [ ] Measurement uncertainty and traceability

## H6. Electronics and power ◑
- [ ] Basic circuits, decoupling, star grounding
- [ ] **Noise:** stepper drivers are loud, encoders are sensitive — layout and shielding matter
- [ ] Power budget; battery behaviour in the cold
- [ ] Connectors, strain relief, and **cable drag as a genuine error source on mounts**

## H7. Manufacturing ◑
- [ ] 3D print dimensional accuracy: shrinkage, warp, anisotropy, orientation strategy
- [ ] Calibration prints and per-axis compensation
- [ ] **Measuring your own printer's accuracy** — the ±100 µm assumption behind the whole
      150 arcsec transmission-error estimate is currently unverified
- [ ] Design for printing: heat-set inserts, avoiding supports on functional faces
- [ ] Basic metalwork: drilling, tapping, reaming
- [ ] **How to specify a machined part** so a shop can quote it

## H8. Field practice ◔
- [ ] Polar alignment methods in practice (drift, plate solve, polar scope)
- [ ] Guiding in practice: calibration, aggressiveness, minimum move
- [ ] Dithering, registration, stacking — and why they *hide* the errors you're trying to measure
- [ ] Session workflow, cool-down, dew

---

# Suggested path and checkpoints

| Phase | Topics | Outcome |
|---|---|---|
| 1 | S1, S2 | You can measure star positions with known uncertainty. **Uses existing images, no hardware, no money.** |
| 2 | S3, S4.1–4.3, S5 | You can compute a polar axis from your own plate solutions |
| 3 | *Checkpoint* | Run SharpCap/N.I.N.A. polar alignment on current gear. Compare to your own code. **Validates the whole premise.** |
| 4 | S6, S7 | You can design and simulate the control loop |
| 5 | S8, S9 | Firmware that moves a motor at a commanded rate and streams telemetry |
| 6 | S10 | Dashboard |
| 7 | H1–H5 | Enough to design the bench drive rig |
| 8 | *Decision gate* | Build the bench rig. Measure transmission error. **Decide whether printed cycloidal survives** |
| 9 | H6–H8 | Full mount |

**Two things to do first, needing neither hardware nor money:** Phase 1, and the Phase 3
checkpoint on your current setup.

---

## Scope warnings — read before starting

1. **This is a multi-year curriculum if taken completely.** That's fine as a learning project,
   but decide consciously whether the goal is a working tracker or the education. They pull in
   different directions, and the honest answer may change partway through.
2. **S4.4 (blind plate solving) and S8 (firmware) are the two genuine time sinks.** Both have
   excellent open-source implementations. The natural checkpoints are: build S4.3 to understand
   the geometry, then use ASTAP; build a minimal step generator, then consider OnStep.
3. **The riskiest hardware assumption is still unverified** — the ±100 µm print accuracy behind
   the 150 arcsec transmission-error estimate. H7 tells you whether that number is real, and
   it's cheap to check with calibration prints long before any mount exists.
4. **Don't build hardware you can't measure.** The ordering above is not arbitrary: every
   hardware phase depends on a software capability that verifies it.
