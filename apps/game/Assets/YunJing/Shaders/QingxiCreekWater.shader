// Creek water for the novice village (Claude Code, K1). Works on the creek ribbon mesh made by
// QingxiNoviceVillageBuilder.Creek: uv.x runs 0..1 across the stream, uv.y along it (1 unit = 4 m, growing
// downstream). Everything is procedural (no textures to download):
//   - two layers of ripples drifting downstream, perturbing the normal;
//   - shallow-to-deep colour across the stream (banks clear, middle dark);
//   - sky reflection at grazing angles (Fresnel), sun glints from the main light;
//   - broken foam along both banks;
//   - Unity fog, so the far creek fades with the land.
Shader "YunJing/QingxiCreekWater"
{
    Properties
    {
        _Shallow ("Shallow colour", Color) = (0.27, 0.53, 0.50, 1)
        _Deep ("Deep colour", Color) = (0.06, 0.26, 0.28, 1)
        _Sky ("Sky reflection", Color) = (0.72, 0.82, 0.88, 1)
        _Foam ("Foam colour", Color) = (0.93, 0.95, 0.94, 1)
        _Width ("Stream width (m)", Float) = 4
        _Speed ("Flow speed (m/s)", Float) = 0.6
        _Ripple ("Ripple strength", Range(0, 1)) = 0.35
        _Gloss ("Sun glint sharpness", Range(16, 512)) = 160
        _AlphaBank ("Opacity at the banks", Range(0, 1)) = 0.45
        _AlphaMid ("Opacity mid-stream", Range(0, 1)) = 0.86
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            Name "Water"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Shallow, _Deep, _Sky, _Foam;
                float _Width, _Speed, _Ripple, _Gloss, _AlphaBank, _AlphaMid;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                float fogCoord : TEXCOORD2;
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS;
                o.positionWS = p.positionWS;
                o.uv = v.uv;
                o.fogCoord = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            float hash(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }

            float noise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                float2 u = f * f * (3 - 2 * f);
                return lerp(lerp(hash(i), hash(i + float2(1, 0)), u.x), lerp(hash(i + float2(0, 1)), hash(i + float2(1, 1)), u.x), u.y);
            }

            // Ripple height in metres-space: a slow broad layer and a fast fine one, both drifting downstream.
            float ripples(float2 m)
            {
                float t = _Time.y * _Speed;
                return noise(m * float2(1.3, 0.7) - float2(0, t * 1.2)) * 0.65
                     + noise(m * float2(3.1, 1.9) + float2(t * 0.15, -t * 2.1)) * 0.35;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float2 m = float2(i.uv.x * _Width, i.uv.y * 4);          // metres across / along
                const float e = 0.08;
                float h = ripples(m);
                float dx = (ripples(m + float2(e, 0)) - h) / e, dz = (ripples(m + float2(0, e)) - h) / e;
                float3 n = normalize(float3(-dx * _Ripple, 1, -dz * _Ripple));

                float3 view = normalize(GetWorldSpaceViewDir(i.positionWS));
                float fresnel = pow(1 - saturate(dot(n, view)), 4);
                float middle = 1 - abs(i.uv.x * 2 - 1);                    // 0 at the banks, 1 mid-stream
                half3 colour = lerp(_Shallow.rgb, _Deep.rgb, smoothstep(0.05, 0.85, middle));
                colour = lerp(colour, _Sky.rgb, saturate(fresnel * 0.45 + 0.04));

                Light sun = GetMainLight();
                float3 halfway = normalize(sun.direction + view);
                colour += sun.color * pow(saturate(dot(n, halfway)), _Gloss) * 1.6;
                colour *= lerp(0.75, 1, saturate(dot(n, sun.direction)));

                // Foam: a band along each bank, broken up by the moving ripples.
                float bank = min(i.uv.x, 1 - i.uv.x);
                float foam = (1 - smoothstep(0.02, 0.13, bank)) * smoothstep(0.42, 0.62, noise(m * 2.4 - float2(0, _Time.y * _Speed * 1.5)) + h * 0.3);
                colour = lerp(colour, _Foam.rgb, foam * 0.85);

                float alpha = saturate(lerp(_AlphaBank, _AlphaMid, smoothstep(0, 0.6, middle)) + fresnel * 0.2 + foam * 0.5);
                colour = MixFog(colour, i.fogCoord);
                return half4(colour, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
