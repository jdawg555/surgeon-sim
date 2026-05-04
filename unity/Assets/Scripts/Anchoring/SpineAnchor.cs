using UnityEngine;
using UnityEngine.InputSystem;

namespace Dragonfly.XR.Anchoring
{
    // Locks a spine reference model to a real-world point on the mannequin / table.
    //
    // Anchoring strategy for the demo:
    //   1. Surgeon points at the mannequin's pelvis with the right controller
    //      and pulls the trigger. That point becomes the L5-S1 origin.
    //   2. Surgeon points at C7 / base of neck and pulls again. That defines
    //      the cranial direction.
    //   3. The model's local frame is built from those two points + world up.
    //
    // No SLAM tricks needed — Quest 3's controller pose tracking is sub-mm
    // stable in a small volume, which is enough for a tabletop mannequin demo.
    //
    // Trigger is read via the new Input System (XRI binding
    // <XRController>{RightHand}/triggerPressed). Wire in the inspector or
    // via the included InputActionReference field; falls back to keyboard
    // Space in the editor for fast iteration.
    [DefaultExecutionOrder(-10)]
    public class SpineAnchor : MonoBehaviour
    {
        public Transform spineRoot;
        public Transform rightController;
        public InputActionReference triggerAction;

        Vector3? _caudal;
        Vector3? _cranial;

        public bool IsAnchored => _caudal.HasValue && _cranial.HasValue;

        void OnEnable() => triggerAction?.action?.Enable();
        void OnDisable() => triggerAction?.action?.Disable();

        void Update()
        {
            bool fired =
                (triggerAction != null && triggerAction.action.WasPressedThisFrame()) ||
#if UNITY_EDITOR || UNITY_STANDALONE
                Keyboard.current != null && Keyboard.current.spaceKey.wasPressedThisFrame;
#else
                false;
#endif

            if (!fired || rightController == null) return;

            if (!_caudal.HasValue) { _caudal = rightController.position; Debug.Log("[Dragonfly.XR] L5-S1 caudal anchor set"); return; }
            if (!_cranial.HasValue) { _cranial = rightController.position; Debug.Log("[Dragonfly.XR] C7 cranial anchor set"); ApplyAnchor(); return; }

            // Re-anchor: third trigger resets and starts over.
            _caudal = rightController.position;
            _cranial = null;
            Debug.Log("[Dragonfly.XR] Re-anchoring — caudal point reset");
        }

        void ApplyAnchor()
        {
            if (spineRoot == null || !_caudal.HasValue || !_cranial.HasValue) return;

            Vector3 origin = _caudal.Value;
            Vector3 up = (_cranial.Value - _caudal.Value).normalized;
            Quaternion rot = Quaternion.FromToRotation(Vector3.up, up);

            spineRoot.SetPositionAndRotation(origin, rot);
            spineRoot.gameObject.SetActive(true);
        }

        public void Reset()
        {
            _caudal = null;
            _cranial = null;
            if (spineRoot != null) spineRoot.gameObject.SetActive(false);
        }
    }
}
