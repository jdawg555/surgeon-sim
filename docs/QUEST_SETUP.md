# Quest 3 setup

Step-by-step from a clean machine to a `.apk` running on a Quest 3, with
the spine overlay locked to a mannequin and voice control responding.

## Prerequisites (one-time)

- **Unity Hub** + **Unity 6 LTS** (`6000.0.32f1` or newer 6000.0.x)
  - When installing, tick **Android Build Support** including the
    sub-modules **OpenJDK** and **Android SDK & NDK Tools**.
- **Meta Quest 3** with developer mode enabled
  - Pair the headset to the Meta mobile app, then **Headset settings →
    Developer mode → On**. May require creating an organization at
    https://developers.meta.com/horizon/manage/organizations/.
- A **USB-C cable** that supports data, plus **Quest Link** or
  **Meta Quest Developer Hub** (MQDH) for sideloading and log streaming.
  https://developers.meta.com/horizon/downloads/package/oculus-developer-hub-win/

## First open

1. Clone the repo, open Unity Hub, **Add project from disk** → select
   `surgeon-sim/unity/`.
2. Unity will resolve the Meta XR scoped registry on first launch
   (this can take 2–3 minutes; check the Package Manager log if it stalls).
3. Accept the **TextMeshPro Essentials** import dialog when prompted.
4. **Edit → Project Settings → XR Plug-in Management → Android tab** →
   tick **OpenXR**. Under **OpenXR → Feature Groups**, tick **Meta Quest
   Support** and any of the **Meta XR** feature flags you want enabled
   (Passthrough, Hand Tracking, Anchors).
5. Switch platform: **File → Build Profiles → Android → Switch Platform**.

## Sanity check before building

In the editor:

- **Tools → Dragonfly → Run Fit Engine Smoke Test**
  Should log top-3 implants for every spine level. If this fails, the
  problem is in the deterministic core, not in XR — fix it here first.

## Build & run

1. Plug the Quest in, allow USB debugging in the headset prompt.
2. **File → Build Profiles → Android** → confirm Quest 3 appears in **Run
   Device**, hit **Build And Run**.
3. First build is ~3–5 minutes; incremental builds are faster.

When it launches, you'll see the passthrough feed plus a (currently
empty) spine root. Point the right controller at the mannequin's pelvis
and pull the trigger; point at the base of the neck and pull again. The
spine model snaps into place.

## Voice setup

The bundled `VoiceCommandRouter` runs `KeywordRecognizer` on the Windows
editor for fast iteration. On-device voice on Quest needs the Voice SDK:

1. Create a free Wit.ai app at https://wit.ai/ and copy its **Server
   Access Token**.
2. In Unity: **Oculus → Voice SDK → Settings** → paste the token.
3. Add an **AppVoiceExperience** component to your scene root.
4. Wire its `OnFullTranscription` UnityEvent → `VoiceCommandRouter.Dispatch`.
5. Train the Wit app on the phrases listed in
   [VOICE_COMMANDS.md](VOICE_COMMANDS.md) (or just leave it as raw
   transcription — `Dispatch` does plain-string matching).

## Stream-to-OBS

For the Twitch stream:

- **Easy path**: cast the headset feed via the Meta mobile app or
  `scrcpy --otg` (https://github.com/Genymobile/scrcpy), capture the
  cast window in OBS as a Window Capture source.
- **Cleaner path**: add the **KlakSpout** package
  (https://github.com/keijiro/KlakSpout) and add a second camera in the
  scene that renders only the HUD layer to a Spout output. Composite in
  OBS with the headset cast underneath.

## Troubleshooting

- **Black screen on launch**: passthrough not enabled. Check **OpenXR →
  Meta XR → Passthrough** is ticked in feature groups, and that the
  scene's `OVRManager` has `Passthrough Support` set to `Required`.
- **Controllers not tracking**: verify the new Input System is set as
  the active backend (**Project Settings → Player → Other → Active Input
  Handling = Both**).
- **Build fails with "minimum API level"**: Quest 3 needs Android API
  29+. **Player → Other → Minimum API Level → Android 10.0 (API 29)**.
- **Meta XR registry won't resolve**: verify `Packages/manifest.json`
  has `https://npm.developer.oculus.com` under `scopedRegistries` and
  that you're not behind a corporate proxy blocking it.
