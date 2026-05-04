# Demo script (Twitch stream)

Run-of-show for a 30-minute live build / demo.

## Pre-flight

- Quest 3 charged, paired to PC over USB-C (Quest Link or `adb`).
- Mannequin / dummy on the desk, prone, lumbar region facing the headset.
- OBS scene with two sources: Quest mirror (Meta companion app or scrcpy),
  Unity stream camera (Spout receiver).
- Hotkey on the headset: long-press menu = re-center.

## Beats

**0:00 — Cold open.** Headset on, look at the mannequin through passthrough.
No overlays. "This is what a surgeon sees today."

**0:30 — Anchor.** Right trigger on pelvis. Right trigger on base of neck.
Spine reference model snaps in place. "Two points, locked to anatomy."

**2:00 — Voice.** "Show L4 L5." Level highlights. "Show implant." Best-fit
overlay appears with score. Talk through the warnings text.

**5:00 — Step through the procedure.** "Next step." "Next step." "Back."
Show how the HUD on the Twitch overlay tracks alongside the surgeon's view.

**8:00 — Switch level.** "Show L5 S1." Different geometry, different
best-fit implant ranking. Talk about why ProDisc-L beats Maverick at a
14° natural lordosis.

**12:00 — Open the code.** Side-by-side: dragonfly Python `fit_engine.py`
vs the C# port. Run **Tools > Dragonfly > Run Fit Engine Smoke Test**.
Same numbers come out.

**18:00 — Talk about what's missing.** Real DICOM, depth occlusion, hand
tracking. Honest about the gap between "demo" and "FDA-cleared product".

**25:00 — Q&A.**

## Two things to remember on stream

1. **Don't claim clinical accuracy.** Mannequin demo, literature averages,
   no PHI, no patient data. Say it out loud. The receipts-not-credentials
   positioning depends on this.

2. **Show the deterministic core.** The "AI assists, humans confirm" thesis
   works because the fit engine is plain math you can read, not a black-box
   model. Open `FitEngine.cs` on stream. That's the whole point.
