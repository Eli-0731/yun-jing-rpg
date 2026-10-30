// 青溪水工 B：Standard（金屬度流程）＋頂點色相乘。
// Blender 端把石塊凹縫的明暗烘在頂點色 Col（sRGB），這裡乘回反照率，讓凹縫在 Unity 裡同樣變暗。
Shader "Qingxi/StandardVC"
{
    Properties
    {
        _Color ("Color", Color) = (1, 1, 1, 1)
        _MainTex ("Albedo", 2D) = "white" {}
        [Normal] _BumpMap ("Normal Map", 2D) = "bump" {}
        _BumpScale ("Normal Scale", Float) = 1.0
        [Gamma] _Metallic ("Metallic", Range(0, 1)) = 0.0
        _Glossiness ("Smoothness", Range(0, 1)) = 0.2
        [Toggle] _UseVertexColor ("Use Vertex Color", Float) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" }
        LOD 300

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows addshadow
        #pragma target 3.0

        sampler2D _MainTex;
        sampler2D _BumpMap;
        fixed4 _Color;
        half _BumpScale;
        half _Metallic;
        half _Glossiness;
        half _UseVertexColor;

        struct Input
        {
            float2 uv_MainTex;
            float4 color : COLOR;
        };

        void surf (Input IN, inout SurfaceOutputStandard o)
        {
            half3 vc = IN.color.rgb;
            #ifndef UNITY_COLORSPACE_GAMMA
            vc = GammaToLinearSpace(vc);
            #endif
            vc = lerp(half3(1, 1, 1), vc, _UseVertexColor);
            fixed4 c = tex2D(_MainTex, IN.uv_MainTex) * _Color;
            o.Albedo = c.rgb * vc;
            o.Normal = UnpackScaleNormal(tex2D(_BumpMap, IN.uv_MainTex), _BumpScale);
            o.Metallic = _Metallic;
            o.Smoothness = _Glossiness;
            o.Alpha = 1;
        }
        ENDCG
    }
    FallBack "Diffuse"
}
