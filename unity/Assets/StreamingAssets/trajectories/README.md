# StreamingAssets trajectories

Bundled neutral-format instrument paths for editor tests.

- `demo_needle_lift.json` — regenerate from repo root::

      cd python
      PYTHONPATH=. python3 -m simulation_assets.export_demo_trajectory \
        ../unity/Assets/StreamingAssets/trajectories/demo_needle_lift.json

Unity loads these via **Tools > Dragonfly > Load bundled demo trajectory**
(`InstrumentTrajectoryReplay.LoadTrajectoryStreamingAssetsRelativeAsync`),
which resolves `Application.streamingAssetsPath` at runtime.
