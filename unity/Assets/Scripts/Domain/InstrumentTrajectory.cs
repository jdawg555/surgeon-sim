using System;
using System.Collections.Generic;
using UnityEngine;

namespace Dragonfly.XR.Domain
{
    // Mirror of python/simulation_assets/trajectory.py. Field names stay
    // snake_case so JsonUtility can read exported files directly.
    [Serializable]
    public class InstrumentTrajectory
    {
        public string trajectory_id;
        public string instrument_id;
        public string source;
        public string coordinate_frame = "case_mm";
        public string generated_at;
        public List<InstrumentPoseSample> samples = new();

        public bool IsValid => samples != null && samples.Count > 0;

        public float DurationSeconds =>
            IsValid ? Mathf.Max(0f, samples[^1].timestamp_s) : 0f;
    }

    [Serializable]
    public class InstrumentPoseSample
    {
        public float timestamp_s;
        public Vector3Fields position_mm = new();
        public QuaternionFields rotation_xyzw = QuaternionFields.Identity;
        [Range(0f, 1f)] public float gripper;
        public string contact_state = "free";
        public string annotation = "";

        public Vector3 PositionMm => position_mm.ToVector3();
        public Quaternion Rotation => rotation_xyzw.ToQuaternion();
    }

    [Serializable]
    public class Vector3Fields
    {
        public float x;
        public float y;
        public float z;

        public Vector3 ToVector3() => new(x, y, z);
    }

    [Serializable]
    public class QuaternionFields
    {
        public float x;
        public float y;
        public float z;
        public float w = 1f;

        public static QuaternionFields Identity => new() { x = 0f, y = 0f, z = 0f, w = 1f };

        public Quaternion ToQuaternion()
        {
            var q = new Quaternion(x, y, z, w);
            return q == default ? Quaternion.identity : q.normalized;
        }
    }
}

