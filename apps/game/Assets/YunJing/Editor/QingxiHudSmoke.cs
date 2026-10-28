using System;
using System.Reflection;
using QingxiWorld;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace YunJing.Editor
{
    // Checks the menu interaction itself, rather than only compiling the Canvas.
    public static class QingxiHudSmoke
    {
        public static void Verify()
        {
            var root = new GameObject("HUD smoke root");
            var oldEventSystem = EventSystem.current;
            try
            {
                root.AddComponent<CharacterController>();
                var walker = root.AddComponent<QingxiFirstPerson>();
                var hud = root.AddComponent<QingxiHud>();
                hud.walker = walker;
                typeof(QingxiHud).GetMethod("Start", BindingFlags.Instance | BindingFlags.NonPublic)
                    ?.Invoke(hud, null);
                var canvas = root.transform.Find("Qingxi HUD Canvas");
                // Inactive objects cannot be found with GameObject.Find.
                var journal = canvas?.Find("Safe Area/Journey Journal")?.gameObject;
                var button = canvas?.transform.Find("Safe Area/Journey Button")?.GetComponent<Button>();
                if (journal == null || button == null || journal.activeSelf)
                    throw new InvalidOperationException("Qingxi journal did not initialize closed with a button.");
                button.onClick.Invoke();
                if (!journal.activeSelf || Cursor.lockState != CursorLockMode.None)
                    throw new InvalidOperationException("Qingxi journal did not open and release the cursor.");
                button.onClick.Invoke();
                if (journal.activeSelf)
                    throw new InvalidOperationException("Qingxi journal did not close.");
                Debug.Log("QINGXI_HUD_SMOKE_PASS: journal opens and closes using its button action.");
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(root);
                if (EventSystem.current != null && EventSystem.current != oldEventSystem)
                    UnityEngine.Object.DestroyImmediate(EventSystem.current.gameObject);
            }
        }
    }
}
