// 青溪水工 B：半透明流動水面（Built-in 管線，Standard 光照）。
// 溪流（S01 的 ww_stream）、石槽（ww_water）、田面積水（ww_water_still）共用這支著色器，只換材質參數。
//
// 流動：水色貼圖與漣漪法線各取兩層，沿 UV 的 _FlowDir（往下游）用不同速度捲動；
//   第二層縮放不同、方向略偏，兩層交錯就不會像整張圖平移。
// 半透明＋折射：GrabPass 取水面後方畫面，依漣漪法線偏移取樣（折射），再與水色依透明度合成；
//   偏移點若落在水面前方的物體上就退回不偏移，避免把前景拉進水裡。
// 深度淡出與岸邊泡沫：用 _CameraDepthTexture 算水面到底下物體的距離（水厚）；
//   水淺處較透明，貼岸／貼槽壁 _FoamDist 內加一圈隨流動的白色泡沫。
//   攝影機要開深度貼圖（Built-in 有平行光陰影時會自動開；WaterDepthCamera 元件會確保開啟）。
// _QxWaterTimeOffset 為全域時間位移（秒），只給批次截圖逐格推進用；執行時保持 0。
Shader "Qingxi/WaterFlow"
{
    Properties
    {
        _Color ("Tint (A = 透明度)", Color) = (1, 1, 1, 0.8)
        _MainTex ("Water Color", 2D) = "white" {}
        [Normal] _BumpMap ("Ripple Normal", 2D) = "bump" {}
        _BumpScale ("Ripple Strength", Float) = 0.5
        _Glossiness ("Smoothness", Range(0, 1)) = 0.92
        _FlowDir ("Flow Direction (UV)", Vector) = (0, 1, 0, 0)
        _Speed1 ("Layer 1 Speed (UV/s)", Float) = 0.30
        _Speed2 ("Layer 2 Speed (UV/s)", Float) = 0.17
        _Tile2 ("Layer 2 Scale", Float) = 1.73
        _Skew2 ("Layer 2 Side Drift", Float) = 0.12
        _DepthAlpha ("Extra Opacity In Deep Areas", Range(0, 1)) = 0.25
        [Toggle] _UseVertexColor ("Use Vertex Color", Float) = 1
        _Refraction ("Refraction Strength", Range(0, 0.1)) = 0.03
        _FadeDepth ("Depth For Full Tint (m)", Float) = 0.35
        _FoamDist ("Shore Foam Width (m)", Float) = 0.06
        _FoamStrength ("Shore Foam Strength", Range(0, 1)) = 0.6
        _FoamColor ("Foam Color", Color) = (0.92, 0.95, 0.93, 1)
    }
    SubShader
    {
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        LOD 300
        ZWrite Off

        GrabPass { "_QxWaterGrab" }

        CGPROGRAM
        #pragma surface surf Standard vertex:vert nolightmap nodynlightmap nodirlightmap
        #pragma target 3.0
        #include "UnityCG.cginc"

        sampler2D _MainTex;
        float4 _MainTex_ST;
        sampler2D _BumpMap;
        sampler2D _QxWaterGrab;
        UNITY_DECLARE_DEPTH_TEXTURE(_CameraDepthTexture);
        fixed4 _Color;
        half _BumpScale;
        half _Glossiness;
        float4 _FlowDir;
        float _Speed1;
        float _Speed2;
        float _Tile2;
        float _Skew2;
        half _DepthAlpha;
        half _UseVertexColor;
        half _Refraction;
        float _FadeDepth;
        float _FoamDist;
        half _FoamStrength;
        fixed4 _FoamColor;
        float _QxWaterTimeOffset;

        struct Input
        {
            float2 flowUv;
            float4 grabPos;                 // xyw：GrabPass 取樣座標；z：水面眼距（m）
            float4 screenPos;               // 深度貼圖取樣座標（Unity 自動填入）
            float4 color : COLOR;
        };

        void vert (inout appdata_full v, out Input o)
        {
            UNITY_INITIALIZE_OUTPUT(Input, o);
            o.flowUv = TRANSFORM_TEX(v.texcoord.xy, _MainTex);
            float4 clip = UnityObjectToClipPos(v.vertex);
            o.grabPos = ComputeGrabScreenPos(clip);
            o.grabPos.z = -UnityObjectToViewPos(v.vertex).z;        // 水面眼距（m）
        }

        float SceneEye(float2 uv)
        {
            return LinearEyeDepth(SAMPLE_DEPTH_TEXTURE(_CameraDepthTexture, uv));
        }

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            float t = _Time.y + _QxWaterTimeOffset;
            float2 dir = normalize(_FlowDir.xy + 1e-5);
            float2 side = float2(-dir.y, dir.x);
            // 取樣座標減去位移＝圖案往 +dir（下游）移動
            float2 uv1 = IN.flowUv - dir * (_Speed1 * t);
            float2 uv2 = IN.flowUv * _Tile2 + float2(0.37, 0.61) - (dir + side * _Skew2) * (_Speed2 * t);

            fixed4 c1 = tex2D(_MainTex, uv1);
            fixed4 c2 = tex2D(_MainTex, uv2);
            fixed4 c = (c1 + c2) * 0.5 * _Color;
            half3 n1 = UnpackScaleNormal(tex2D(_BumpMap, uv1), _BumpScale);
            half3 n2 = UnpackScaleNormal(tex2D(_BumpMap, uv2), _BumpScale);
            half3 n = normalize(half3(n1.xy + n2.xy, n1.z * n2.z));

            half3 vc = IN.color.rgb;
            #ifndef UNITY_COLORSPACE_GAMMA
            vc = GammaToLinearSpace(vc);
            #endif
            vc = lerp(half3(1, 1, 1), vc, _UseVertexColor);
            half deep = 1 - saturate(dot(vc, half3(0.333, 0.333, 0.334)));   // 頂點色越暗＝越深

            // 水厚：畫面深度 − 水面深度（沿視線）
            float2 duv = IN.screenPos.xy / IN.screenPos.w;
            float2 guv = IN.grabPos.xy / IN.grabPos.w;
            float surfEye = IN.grabPos.z;
            float thick = max(0, SceneEye(duv) - surfEye);

            // 折射：偏移量隨水厚增加（貼岸處不偏，避免岸線錯位）
            float2 ofs = n.xy * _Refraction * saturate(thick / max(_FadeDepth, 1e-3));
            // GrabPass 與深度貼圖在 D3D 渲染到 RT 時 y 可能上下相反：兩者 y 不同就把深度端的偏移 y 反向
            float flipY = abs(guv.y - duv.y) < 1e-3 ? 1 : -1;
            if (SceneEye(duv + ofs * float2(1, flipY)) < surfEye) ofs = 0;   // 偏到前景物體上：不偏移
            half3 behind = tex2D(_QxWaterGrab, guv + ofs).rgb;

            half a = saturate(_Color.a + _DepthAlpha * deep);
            a *= lerp(0.35, 1.0, saturate(thick / max(_FadeDepth, 1e-3)));   // 淺處更透明

            // 岸邊泡沫：貼岸帶 × 流動的亮紋（兩層水色的亮部）
            half shore = 1 - saturate(thick / max(_FoamDist, 1e-3));
            half streak = saturate((max(c1.r, c2.g) - 0.45) * 3.0);
            half foam = saturate(shore * (0.45 + streak) * _FoamStrength);

            o.Albedo = lerp(c.rgb * vc * a, _FoamColor.rgb, foam);   // 水色依透明度受光；泡沫不透明
            o.Emission = behind * (1 - a) * (1 - foam);               // 後方畫面已含光照：直接加回
            o.Normal = n;
            o.Metallic = 0;
            o.Smoothness = lerp(_Glossiness, 0.3, foam);
            o.Alpha = 1;
        }
        ENDCG
    }
    FallBack "Transparent/Diffuse"
}
