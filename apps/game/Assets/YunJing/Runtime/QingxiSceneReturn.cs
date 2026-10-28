using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

namespace YunJing
{
    // Added to joshsu54's generated AlchemyRoom scene by the novice-village build: a way back out to
    // the Qingxi street. Does not touch the workshop, its API session or its inventory results.
    public sealed class QingxiSceneReturn : MonoBehaviour
    {
        public static string ReturnScene = QingxiAbcStations.VillageScene;
        GUIStyle style;

        void Start() { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }

        void Update()
        {
            if (Keyboard.current != null && Keyboard.current.backspaceKey.wasPressedThisFrame) Leave();
        }

        void OnGUI()
        {
            if (string.IsNullOrEmpty(ReturnScene) || !Application.CanStreamedLevelBeLoaded(ReturnScene)) return;
            if (style == null) style = new GUIStyle(GUI.skin.button) { fontSize = 18 };
            var s = Screen.safeArea;
            if (GUI.Button(new Rect(s.xMin + 16, Screen.height - s.yMax + 16, 220, 46), "← 返回青溪  [Backspace]", style)) Leave();
        }

        public void Leave()
        {
            if (string.IsNullOrEmpty(ReturnScene) || !Application.CanStreamedLevelBeLoaded(ReturnScene)) return;
            QingxiAbcStations.ReturningFromAlchemy = true;
            SceneManager.LoadScene(ReturnScene);
        }
    }
}
