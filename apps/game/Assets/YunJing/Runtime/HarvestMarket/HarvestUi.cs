using System;
using UnityEngine;
using UnityEngine.UI;
using YunJing.Alchemy;

namespace YunJing.HarvestMarket
{
    // The alchemy panel's bamboo-slip uGUI (AlchemyUi), with the HUD's Noto Sans TC and touch targets of at least
    // 88 × 88 px on the 1920 × 1080 reference canvas.
    public static class HarvestUi
    {
        public const float Touch = 96;   // ≥ 88 px at 1080p

        public static Font Font => QingxiFonts.Ui != null ? QingxiFonts.Ui : AlchemyUi.Font;

        public static Text Label(string name, Transform parent, string text, int size, TextAnchor anchor, Color color)
        {
            var label = AlchemyUi.Label(name, parent, text, size, anchor, color); label.font = Font; return label;
        }

        /// A button anchored inside its parent by pixel offsets, never smaller than Touch on either side.
        public static Button Button(string name, Transform parent, string text, Action onClick, Vector2 anchor, Vector2 position, Vector2 size, Color? color = null, int font = 30)
        {
            var b = AlchemyUi.Button(name, parent, text, onClick, color, font);
            var rt = (RectTransform)b.transform; rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor;
            rt.sizeDelta = new Vector2(Mathf.Max(Touch, size.x), Mathf.Max(Touch, size.y)); rt.anchoredPosition = position;
            b.GetComponentInChildren<Text>().font = Font;
            return b;
        }

        public static Image Sprite(string name, Transform parent, Sprite sprite, Vector2 size)
        {
            var rt = AlchemyUi.Rect(name, parent, new Vector2(.5f, .5f), new Vector2(.5f, .5f), Vector2.zero, Vector2.zero);
            rt.sizeDelta = size; var img = rt.gameObject.AddComponent<Image>(); img.sprite = sprite; img.preserveAspect = true; return img;
        }

        public static RectTransform Fixed(RectTransform rt, Vector2 anchor, Vector2 position, Vector2 size)
        {
            rt.anchorMin = rt.anchorMax = anchor; rt.pivot = anchor; rt.sizeDelta = size; rt.anchoredPosition = position; return rt;
        }

        public static Canvas Canvas(string name, int order)
        {
            var c = AlchemyUi.Canvas(name); c.sortingOrder = order; return c;
        }
    }
}
