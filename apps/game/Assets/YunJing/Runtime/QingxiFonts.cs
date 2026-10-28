using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace YunJing
{
    // Bundled Chinese fonts (Google Noto, SIL Open Font License; see Resources/Fonts/OFL-*.txt). The built-in
    // LegacyRuntime font has no CJK glyphs and a browser (WebGL/PWA) has no OS font to fall back on, so every
    // label would be blank there. Noto Sans TC is the UI face, Noto Serif TC the title and place-name face.
    public static class QingxiFonts
    {
        static Font ui, title;
        public static Font Ui => ui != null ? ui : ui = Resources.Load<Font>("Fonts/NotoSansTC-Variable");
        public static Font Title => title != null ? title : title = Resources.Load<Font>("Fonts/NotoSerifTC-Variable") ?? Ui;

        // Call at the top of OnGUI: IMGUI draws with the shared default skin.
        public static void ApplyImgui()
        {
            if (Ui != null && GUI.skin.font != Ui) GUI.skin.font = Ui;
        }

        // uGUI Text with the glyph-less built-in font switches to Noto Sans TC. In the browser every other font
        // (for example joshsu54's alchemy UI, which asks the OS for JhengHei) switches too, since none exist there.
        public static void ApplyToTexts()
        {
            if (Ui == null) return;
            bool browser = Application.platform == RuntimePlatform.WebGLPlayer;
            foreach (var text in Object.FindObjectsByType<Text>(FindObjectsInactive.Include, FindObjectsSortMode.None))
            {
                if (text.font == Ui || text.font == Title) continue;
                if (text.font == null || browser || text.font.name.StartsWith("LegacyRuntime") || text.font.name == "Arial") text.font = Ui;
            }
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Install()
        {
            var runner = new GameObject("Qingxi fonts").AddComponent<Runner>();
            Object.DontDestroyOnLoad(runner.gameObject);
            SceneManager.sceneLoaded += (_, _) => runner.Sweep();
            runner.Sweep();
        }

        // UI built in Start() or a moment later still gets the font: sweep right away and again shortly after.
        sealed class Runner : MonoBehaviour
        {
            public void Sweep() { StopAllCoroutines(); StartCoroutine(Sweeps()); }
            IEnumerator Sweeps()
            {
                ApplyToTexts();
                foreach (var wait in new[] { .2f, 1f, 3f }) { yield return new WaitForSecondsRealtime(wait); ApplyToTexts(); }
                // In the browser, panels that appear later (alchemy recipes, results) keep getting the font.
                while (Application.platform == RuntimePlatform.WebGLPlayer) { yield return new WaitForSecondsRealtime(1.5f); ApplyToTexts(); }
            }
        }
    }
}
