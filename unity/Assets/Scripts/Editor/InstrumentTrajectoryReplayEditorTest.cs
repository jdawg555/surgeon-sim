#if UNITY_EDITOR
using Dragonfly.XR.Simulation;
using UnityEditor;
using UnityEngine;

namespace Dragonfly.XR.EditorTools
{
    // Tools > Dragonfly > Load Instrument Trajectory...
    // Loads a trajectory JSON exported by python/simulation_assets and
    // replays it on a simple scene object for headset-free verification.
    public static class InstrumentTrajectoryReplayEditorTest
    {
        const string HostName = "__instrument_trajectory_replay_test";

        [MenuItem("Tools/Dragonfly/Load Instrument Trajectory...")]
        public static async void LoadTrajectoryFromDisk()
        {
            var path = EditorUtility.OpenFilePanel(
                "Pick an instrument trajectory JSON", "", "json");
            if (string.IsNullOrEmpty(path)) return;

            var host = GameObject.Find(HostName);
            if (host == null)
            {
                host = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                host.name = HostName;
                host.transform.localScale = new Vector3(0.01f, 0.04f, 0.01f);
            }

            var replay = host.GetComponent<InstrumentTrajectoryReplay>();
            if (replay == null) replay = host.AddComponent<InstrumentTrajectoryReplay>();
            replay.Target = host.transform;
            replay.PlayOnLoad = false;

            var ok = await replay.LoadTrajectoryAsync(path);
            if (!ok) return;

            replay.ApplyAtTime(replay.Trajectory.DurationSeconds);
            Selection.activeGameObject = host;
            EditorGUIUtility.PingObject(host);
            Debug.Log(
                $"[InstrumentTrajectoryReplay] OK loaded {replay.Trajectory.trajectory_id} " +
                $"duration={replay.Trajectory.DurationSeconds:F2}s from {path}");
        }

        [MenuItem("Tools/Dragonfly/Load bundled demo trajectory (StreamingAssets)")]
        public static async void LoadBundledDemoTrajectory()
        {
            var host = GameObject.Find(HostName);
            if (host == null)
            {
                host = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                host.name = HostName;
                host.transform.localScale = new Vector3(0.01f, 0.04f, 0.01f);
            }

            var replay = host.GetComponent<InstrumentTrajectoryReplay>();
            if (replay == null) replay = host.AddComponent<InstrumentTrajectoryReplay>();
            replay.Target = host.transform;
            replay.PlayOnLoad = false;

            var ok = await replay.LoadTrajectoryStreamingAssetsRelativeAsync(
                "trajectories/demo_needle_lift.json");
            if (!ok) return;

            replay.ApplyAtTime(replay.Trajectory.DurationSeconds);
            Selection.activeGameObject = host;
            EditorGUIUtility.PingObject(host);
            Debug.Log(
                $"[InstrumentTrajectoryReplay] OK bundled demo {replay.Trajectory.trajectory_id} " +
                $"duration={replay.Trajectory.DurationSeconds:F2}s");
        }

        [MenuItem("Tools/Dragonfly/Clear Instrument Trajectory")]
        public static void ClearTrajectoryTest()
        {
            var host = GameObject.Find(HostName);
            if (host == null) return;
            Object.DestroyImmediate(host);
            Debug.Log("[InstrumentTrajectoryReplay] cleared");
        }
    }
}
#endif

