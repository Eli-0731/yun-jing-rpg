// Wind for trees, bamboo, reeds and shrubs (Claude Code, K2). Works on any model, whatever its import rotation:
// the sway weight is the vertex's height above the model's origin in world space (0 at the base, 1 at _Height),
// squared so trunks stay put and tips move most. If the model has vertex colours, red multiplies the weight
// (C8-C10 models store their own wind weights there; white = no change).
// Lighting: main light with shadows, ambient (SH), fog; two-sided leaves; shadow and depth passes sway too.
Shader "YunJing/QingxiFoliageWind"
{
    Properties
    {
        _BaseMap ("Base map", 2D) = "white" {}
        _BaseColor ("Base colour", Color) = (1, 1, 1, 1)
        _Cutoff ("Alpha cut-off", Range(0, 1)) = 0.4
        _Height ("Sway height (m)", Float) = 5
        _Strength ("Sway (m at the top)", Float) = 0.18
        _Flutter ("Leaf flutter (m)", Float) = 0.025
        _WindDir ("Wind direction (xz)", Vector) = (1, 0, 0.35, 0)
        [Toggle] _UseVertexColour ("Vertex colour red = wind weight", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "Queue" = "AlphaTest" "RenderPipeline" = "UniversalPipeline" }
        Cull Off

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half4 _BaseColor;
            half _Cutoff;
            float _Height, _Strength, _Flutter;
            float4 _WindDir;
            float _UseVertexColour;
        CBUFFER_END
        TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);

        float3 Sway(float3 positionWS, float4 colour)
        {
            float3 origin = float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m13, UNITY_MATRIX_M._m23);
            float k = saturate((positionWS.y - origin.y) / max(_Height, 0.01));
            k = k * k * lerp(1, colour.r, _UseVertexColour);
            float phase = origin.x * 0.35 + origin.z * 0.22;
            float t = _Time.y;
            float gust = sin(t * 1.6 + phase) * 0.6 + sin(t * 3.1 + phase * 1.3) * 0.25 + 0.15;
            float2 dir = normalize(_WindDir.xz + 1e-4);
            float3 offset = float3(dir.x, 0, dir.y) * gust * _Strength * k;
            // Small fast flutter so leaves shimmer even when the gust is calm.
            offset += sin(t * 7.0 + dot(positionWS, float3(3.1, 1.7, 2.3))) * _Flutter * k * float3(0.6, 0.3, 0.6);
            return positionWS + offset;
        }

        half Clip(float2 uv)
        {
            half4 c = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, uv) * _BaseColor;
            clip(c.a - _Cutoff);
            return c.a;
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; float4 colour : COLOR; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                float3 normalWS : TEXCOORD2;
                float fogCoord : TEXCOORD3;
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = Sway(TransformObjectToWorld(v.positionOS.xyz), v.colour);
                o.positionWS = ws;
                o.positionCS = TransformWorldToHClip(ws);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                return o;
            }

            half4 frag(Varyings i, bool front : SV_IsFrontFace) : SV_Target
            {
                half4 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv) * _BaseColor;
                clip(albedo.a - _Cutoff);
                float3 n = normalize(i.normalWS) * (front ? 1 : -1);
                Light sun = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
                // Wrapped diffuse: leaves pass light through, so the shaded side never goes black.
                half wrap = saturate((dot(n, sun.direction) + 0.35) / 1.35);
                half3 lit = albedo.rgb * (sun.color * wrap * sun.shadowAttenuation * sun.distanceAttenuation + SampleSH(n));
                return half4(MixFog(lit, i.fogCoord), 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On ColorMask 0
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"
            float3 _LightDirection;
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; float4 colour : COLOR; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = Sway(TransformObjectToWorld(v.positionOS.xyz), v.colour);
                float3 n = TransformObjectToWorldNormal(v.normalOS);
                o.positionCS = TransformWorldToHClip(ApplyShadowBias(ws, n, _LightDirection));
                #if UNITY_REVERSED_Z
                    o.positionCS.z = min(o.positionCS.z, UNITY_NEAR_CLIP_VALUE);
                #else
                    o.positionCS.z = max(o.positionCS.z, UNITY_NEAR_CLIP_VALUE);
                #endif
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(Varyings i) : SV_Target { Clip(i.uv); return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On ColorMask R
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; float4 colour : COLOR; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformWorldToHClip(Sway(TransformObjectToWorld(v.positionOS.xyz), v.colour));
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                return o;
            }
            half4 frag(Varyings i) : SV_Target { Clip(i.uv); return 0; }
            ENDHLSL
        }
    }
    FallBack Off
}
