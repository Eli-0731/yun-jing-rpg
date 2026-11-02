// One material for the sick boar (BR01) and the pine it runs into (BR02) (Johnnnny0823). The base map is the healthy look;
// _MaskMap holds the states, so nothing needs a second mesh or a texture swap:
//   R = where the dark qi seeps through the fur, in order: the highest values are the last to clear as _Zhuo falls
//   G = the eyes' red
//   B = the pale scraped bark
// _Zhuo: 1 = sick, 0 = an ordinary warm brown boar. _Scar: 0 = whole bark, 1 = scraped.
// Lighting matches YunJing/QingxiFoliageWind (main light with shadows, ambient SH, fog, wrapped diffuse), with the wind
// on when _Strength > 0 (the pine's needles). _FurMap is read through the second UV and alpha-clips the boar's fur tufts;
// everything else sits in its opaque column, and the pine leaves it white.
Shader "YunJing/QingxiZhuoBoar"
{
    Properties
    {
        _BaseMap ("Base map", 2D) = "white" {}
        [Normal] _NormalMap ("Normal map", 2D) = "bump" {}
        _OrmMap ("AO, roughness, metal", 2D) = "white" {}
        _MaskMap ("Mask (R dark qi, G eye, B scar)", 2D) = "black" {}
        _FurMap ("Fur tufts (A cuts, RGB shades; second UV)", 2D) = "white" {}
        _Zhuo ("Dark qi (0-1)", Range(0, 1)) = 1
        _Scar ("Scar (0-1)", Range(0, 1)) = 0
        _ZhuoDark ("Dark qi, deep", Color) = (0.085, 0.022, 0.185, 1)
        _ZhuoLight ("Dark qi, thin", Color) = (0.2, 0.055, 0.36, 1)
        _EyeColour ("Sick eye", Color) = (0.36, 0.05, 0.05, 1)
        _ScarColour ("Scar", Color) = (0.5, 0.33, 0.16, 1)
        _Wrap ("Wrapped diffuse", Range(0, 1)) = 0.2
        _Height ("Sway height (m)", Float) = 5
        _Strength ("Sway (m at the top)", Float) = 0
        _Flutter ("Needle flutter (m)", Float) = 0
        _WindDir ("Wind direction (xz)", Vector) = (1, 0, 0.35, 0)
    }
    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "Queue" = "AlphaTest" "RenderPipeline" = "UniversalPipeline" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        CBUFFER_START(UnityPerMaterial)
            float4 _BaseMap_ST;
            half _Zhuo, _Scar, _Wrap;
            half4 _ZhuoDark, _ZhuoLight, _EyeColour, _ScarColour;
            float _Height, _Strength, _Flutter;
            float4 _WindDir;
        CBUFFER_END
        TEXTURE2D(_FurMap); SAMPLER(sampler_FurMap);

        void ClipFur(float2 uv2) { clip(SAMPLE_TEXTURE2D(_FurMap, sampler_FurMap, uv2).a - 0.5); }

        float3 Sway(float3 positionWS)
        {
            if (_Strength <= 0 && _Flutter <= 0) return positionWS;
            float3 origin = float3(UNITY_MATRIX_M._m03, UNITY_MATRIX_M._m13, UNITY_MATRIX_M._m23);
            float k = saturate((positionWS.y - origin.y) / max(_Height, 0.01));
            k *= k;
            float phase = origin.x * 0.35 + origin.z * 0.22, t = _Time.y;
            float gust = sin(t * 1.6 + phase) * 0.6 + sin(t * 3.1 + phase * 1.3) * 0.25 + 0.15;
            float2 dir = normalize(_WindDir.xz + 1e-4);
            float3 offset = float3(dir.x, 0, dir.y) * gust * _Strength * k;
            offset += sin(t * 7.0 + dot(positionWS, float3(3.1, 1.7, 2.3))) * _Flutter * k * float3(0.6, 0.3, 0.6);
            return positionWS + offset;
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
            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_NormalMap); TEXTURE2D(_OrmMap); TEXTURE2D(_MaskMap);

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float2 uv2 : TEXCOORD1; half4 colour : COLOR; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                float3 normalWS : TEXCOORD2;
                float4 tangentWS : TEXCOORD3;
                float fogCoord : TEXCOORD4;
                half3 colour : COLOR;
                float2 uv2 : TEXCOORD5;
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = Sway(TransformObjectToWorld(v.positionOS.xyz));
                o.positionWS = ws;
                o.positionCS = TransformWorldToHClip(ws);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.tangentWS = float4(TransformObjectToWorldDir(v.tangentOS.xyz), v.tangentOS.w * GetOddNegativeScale());
                o.uv = TRANSFORM_TEX(v.uv, _BaseMap);
                o.fogCoord = ComputeFogFactor(o.positionCS.z);
                o.colour = v.colour.rgb;
                o.uv2 = v.uv2;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 tuft = SAMPLE_TEXTURE2D(_FurMap, sampler_FurMap, i.uv2);
                clip(tuft.a - 0.5);
                half3 albedo = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * i.colour * tuft.rgb;   // fur root-to-tip shade, per strand
                half3 mask = SAMPLE_TEXTURE2D(_MaskMap, sampler_BaseMap, i.uv).rgb;
                half3 orm = SAMPLE_TEXTURE2D(_OrmMap, sampler_BaseMap, i.uv).rgb;

                // The veins retreat into their deepest strands as _Zhuo falls, then vanish.
                half vein = smoothstep(1 - _Zhuo, 1 - _Zhuo + 0.5, mask.r) * step(0.001, _Zhuo) * step(0.02, mask.r);
                half3 qi = lerp(_ZhuoLight.rgb, _ZhuoDark.rgb, saturate(mask.r * 1.4));
                albedo = lerp(albedo, qi, vein * 0.92);
                albedo = lerp(albedo, _EyeColour.rgb, mask.g * _Zhuo);
                albedo = lerp(albedo, _ScarColour.rgb * (0.82 + 0.18 * mask.b), smoothstep(0.15, 0.6, mask.b) * _Scar);

                float3 n = normalize(i.normalWS);
                float3 t = normalize(i.tangentWS.xyz), b = cross(n, t) * i.tangentWS.w;
                half3 tn = UnpackNormal(SAMPLE_TEXTURE2D(_NormalMap, sampler_BaseMap, i.uv));
                n = normalize(t * tn.x + b * tn.y + n * tn.z);

                Light sun = GetMainLight(TransformWorldToShadowCoord(i.positionWS));
                half wrap = saturate((dot(n, sun.direction) + _Wrap) / (1 + _Wrap));
                half3 lit = albedo * (sun.color * wrap * sun.shadowAttenuation * sun.distanceAttenuation + SampleSH(n) * orm.r);
                lit += qi * vein * 0.16;   // stays violet in shade, where a dark stain would read as blood
                float3 view = normalize(GetWorldSpaceViewDir(i.positionWS));
                float3 h = normalize(sun.direction + view);
                lit += sun.color * sun.shadowAttenuation * pow(saturate(dot(n, h)), lerp(90.0, 6.0, orm.g)) * (1 - orm.g) * 0.25;
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
            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv2 : TEXCOORD1; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv2 : TEXCOORD0; };
            Varyings vert(Attributes v)
            {
                Varyings o;
                float3 ws = Sway(TransformObjectToWorld(v.positionOS.xyz));
                float4 cs = TransformWorldToHClip(ApplyShadowBias(ws, TransformObjectToWorldNormal(v.normalOS), _LightDirection));
                #if UNITY_REVERSED_Z
                    cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
                #else
                    cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
                #endif
                o.positionCS = cs; o.uv2 = v.uv2;
                return o;
            }
            half4 frag(Varyings i) : SV_Target { ClipFur(i.uv2); return 0; }
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
            struct Attributes { float4 positionOS : POSITION; float2 uv2 : TEXCOORD1; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv2 : TEXCOORD0; };
            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformWorldToHClip(Sway(TransformObjectToWorld(v.positionOS.xyz)));
                o.uv2 = v.uv2;
                return o;
            }
            half4 frag(Varyings i) : SV_Target { ClipFur(i.uv2); return 0; }
            ENDHLSL
        }
    }
    FallBack Off
}
