// Work pack B-56h test scene ground: no texture and no seams. Colour comes from world position, so trampled earth
// fades into grass along an uneven edge around the work site and the fields instead of ending at a rectangle.
Shader "YunJing/CreekGround"
{
    Properties
    {
        _GrassA("Grass, dry", Color) = (.15, .19, .075, 1)
        _GrassB("Grass, lush", Color) = (.07, .125, .045, 1)
        _DirtA("Earth, pale", Color) = (.2, .17, .125, 1)
        _DirtB("Earth, dark", Color) = (.135, .112, .083, 1)
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _GrassA, _GrassB, _DirtA, _DirtB;
            CBUFFER_END
            float _CreekNursery;   // protect_nursery keeps a patch of green in the middle of the site

            struct In { float4 positionOS : POSITION; };
            struct Out { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; float fog : TEXCOORD1; };

            Out Vert(In i)
            {
                Out o; VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS; o.fog = 0; return o;
            }

            float hash(float2 p) { return frac(sin(dot(p, float2(127.1, 311.7))) * 43758.5453); }
            float noise(float2 p)
            {
                float2 i = floor(p), f = frac(p), u = f * f * (3 - 2 * f);
                return lerp(lerp(hash(i), hash(i + float2(1, 0)), u.x), lerp(hash(i + float2(0, 1)), hash(i + float2(1, 1)), u.x), u.y);
            }
            float fbm(float2 p) { return noise(p) * .5 + noise(p * 2.03 + 7.1) * .27 + noise(p * 4.1 + 3.3) * .15 + noise(p * 8.3 + 1.9) * .08; }
            float box(float2 q, float2 c, float2 half_) { float2 d = abs(q - c) - half_; return length(max(d, 0)) + min(max(d.x, d.y), 0); }

            float bump(float2 q, float earth) { return fbm(q * 2.7) * .05 + noise(q * 19) * lerp(.008, .014, earth) + noise(q * 57) * .004; }

            half4 Frag(Out i) : SV_Target
            {
                float2 q = i.positionWS.xz;
                float wander = (fbm(q * .9) - .5) * 1.5 + (noise(q * 4.3) - .5) * .28;
                float d = min(min(box(q, float2(0, 2.9), float2(3.5, 3.5)), box(q, float2(0, 11), float2(9.1, 2.1))), box(q, float2(0, 7.6), float2(6.9, 1))) + wander;
                float earth = 1 - smoothstep(-.05, .75, d);
                earth *= 1 - _CreekNursery * (1 - smoothstep(-.12, .3, box(q, float2(1.75, 3.75), float2(.95, .45)) + wander * .35));

                float2 worn = q + 11.3;
                half3 grass = lerp(_GrassA.rgb, _GrassB.rgb, smoothstep(.3, .68, fbm(q * .33)));
                grass *= .78 + .44 * noise(q * 23) * noise(q * 9);
                half3 dirt = lerp(_DirtB.rgb, _DirtA.rgb, smoothstep(.25, .68, fbm(worn * 1.3)));
                dirt *= .9 + .2 * noise(q * 31);
                float pebble = smoothstep(.8, .88, noise(q * 26)) * smoothstep(.4, .7, noise(q * 3.1));
                dirt = lerp(dirt, half3(.36, .33, .28), pebble * .7);
                half3 albedo = lerp(grass, dirt, earth);

                const float e = .01;
                float h = bump(q, earth);
                float3 n = normalize(float3((h - bump(q + float2(e, 0), earth)) / e, 1, (h - bump(q + float2(0, e), earth)) / e));

                InputData v = (InputData)0;
                v.positionWS = i.positionWS; v.positionCS = i.positionCS; v.normalWS = n;
                v.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                v.shadowCoord = TransformWorldToShadowCoord(i.positionWS); v.fogCoord = ComputeFogFactor(TransformWorldToHClip(i.positionWS).z); v.bakedGI = SampleSH(n);
                v.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS); v.shadowMask = half4(1, 1, 1, 1);
                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo; s.smoothness = .08; s.occlusion = 1; s.alpha = 1; s.normalTS = half3(0, 0, 1);
                half4 color = UniversalFragmentPBR(v, s);
                color.rgb = MixFog(color.rgb, v.fogCoord);
                return color;
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
    }
    FallBack "Universal Render Pipeline/Lit"
}
