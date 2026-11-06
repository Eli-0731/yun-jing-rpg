// Running water for the creek repair channels (work pack B-56h). Nothing here is baked into a model and no script
// feeds it: the pattern moves on _Time, so a water mesh flows by itself once it has this material.
// The mesh only supplies coordinates: uv.x 0..1 across the channel, uv.y in metres downstream. That holds for the
// CR06/CR08 *_water FBX and for the waterworks B02..B05 *_water FBX, and the pattern repeats every metre along uv.y
// so pieces of whole-metre length join without a seam.
//   - fast water mid-channel, slower water along the banks;
//   - long flow streaks perturbing the normal, sky reflection at grazing angles, sun glints;
//   - broken foam along both banks and a few flecks carried downstream.
// _Still 1 is for standing field water: uv is metres on both axes, no banks, only a slow lap.
Shader "YunJing/CreekFlowWater"
{
    Properties
    {
        _Shallow ("Shallow colour", Color) = (0.18, 0.255, 0.21, 1)
        _Deep ("Deep colour", Color) = (0.085, 0.16, 0.135, 1)
        _Sky ("Sky reflection", Color) = (0.6, 0.7, 0.76, 1)
        _Foam ("Foam colour", Color) = (0.7, 0.74, 0.68, 1)
        _Width ("Channel width (m)", Float) = 0.4
        _Speed ("Flow speed mid-channel (m/s)", Float) = 0.45
        _Ripple ("Ripple strength", Range(0, 1)) = 0.06
        _Gloss ("Sun glint sharpness", Range(16, 512)) = 220
        _AlphaBank ("Opacity at the banks", Range(0, 1)) = 0.7
        _AlphaMid ("Opacity mid-channel", Range(0, 1)) = 0.9
        _Still ("Standing water", Float) = 0
        _Reveal ("Water front: x, z of the entry, w radius reached", Vector) = (0, 0, 0, 100000)
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            Name "Water"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite On        // strips of one piece overlap at a bend: the second must not blend over the first
            ZTest Less
            Cull Off

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Shallow, _Deep, _Sky, _Foam;
                float _Width, _Speed, _Ripple, _Gloss, _AlphaBank, _AlphaMid, _Still;
                float4 _Reveal;
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

            // Value noise that repeats every `wrap` cells along y.
            float noise(float2 p, float wrap)
            {
                float2 i = floor(p), f = frac(p);
                float2 u = f * f * (3 - 2 * f);
                float y0 = fmod(i.y, wrap), y1 = fmod(i.y + 1, wrap);
                return lerp(lerp(hash(float2(i.x, y0)), hash(float2(i.x + 1, y0)), u.x), lerp(hash(float2(i.x, y1)), hash(float2(i.x + 1, y1)), u.x), u.y);
            }

            // One layer: `across` cells per metre across, `along` whole cells per metre downstream, drifting at `run` x the flow speed.
            float layer(float2 m, float across, float along, float run)
            {
                return noise(float2(m.x * across + along * 7, frac(m.y - _Time.y * _Speed * run) * along), along);
            }

            float height(float2 m, float run) { return layer(m, 20, 3, run) * 0.55 + layer(m, 44, 7, run * 1.3) * 0.3 + layer(m, 90, 15, run * 1.7) * 0.15; }

            float surface(float2 m, float middle)
            {
                // two speeds blended by position, because shearing one pattern would tear it apart over time
                return lerp(height(m, 0.45), height(m, 1), smoothstep(0.1, 0.7, middle));
            }

            half4 frag(Varyings i) : SV_Target
            {
                // the front of the water is not a clean circle: it finds its own way, faster in some places
                float2 wq = i.positionWS.xz;
                float creep = (noise(wq * 2.3, 512) - .5) * .55 + (noise(wq * 7.1 + 3, 512) - .5) * .16;
                float ahead = _Reveal.w - distance(wq, _Reveal.xz) + (_Reveal.w > 9999 ? 1 : creep);
                clip(ahead);
                float still = step(0.5, _Still);
                float2 m = float2(i.uv.x * lerp(_Width, 0.4, still), i.uv.y * lerp(1, 0.4, still));   // metres across / along; a wider lap on still water
                float middle = lerp(saturate(1 - abs(i.uv.x * 2 - 1)), 0.6, still);     // 0 at the banks, 1 mid-channel
                const float e = 0.012;
                float h = surface(m, middle);
                float dx = (surface(m + float2(e, 0), middle) - h) / e, dz = (surface(m + float2(0, e), middle) - h) / e;

                // the flow direction in the world, from the screen derivatives of uv
                float3 dpx = ddx(i.positionWS), dpy = ddy(i.positionWS);
                float2 dux = ddx(i.uv), duy = ddy(i.uv);
                float3 along = (dpy * dux.x - dpx * duy.x) * sign(dux.x * duy.y - dux.y * duy.x);
                along.y = 0;
                along = dot(along, along) > 1e-12 ? normalize(along) : float3(0, 0, 1);
                float3 across = float3(along.z, 0, -along.x);
                float3 n = normalize(float3(0, 1, 0) - (across * dx + along * dz) * _Ripple);

                float3 view = normalize(GetWorldSpaceViewDir(i.positionWS));
                float fresnel = pow(1 - saturate(dot(n, view)), 4);
                half3 colour = still > .5 ? half3(.185, .275, .235) * (.82 + h * .36) : lerp(_Shallow.rgb, _Deep.rgb, saturate(smoothstep(0.02, 0.8, middle) * (0.62 + h * 0.75)));

                // pale lines where the current folds over, running with the water
                float streak = pow(1 - abs(layer(m, 40, 2, 1.15) * 2 - 1), 8) * smoothstep(0.1, 0.6, middle) * (1 - still);
                colour += _Sky.rgb * streak * 0.035;
                colour = lerp(colour, _Sky.rgb, saturate(fresnel * lerp(0.34, 0.45, still) + lerp(0.025, 0.05, still)));

                Light sun = GetMainLight();
                float3 halfway = normalize(sun.direction + view);
                colour += sun.color * pow(saturate(dot(n, halfway)), _Gloss) * 0.55;
                colour *= lerp(0.78, 1, saturate(dot(n, sun.direction)));

                // foam: a broken line along each bank, plus a few flecks carried along
                float bank = min(i.uv.x, 1 - i.uv.x);
                float lip = 1 - smoothstep(0.015, 0.09 + layer(m, 20, 6, 0.3) * 0.08, bank);
                float foam = lip * smoothstep(0.34, 0.62, layer(m, 60, 19, 0.45));
                foam += smoothstep(0.7, 0.95, layer(m, 110, 7, 1.1)) * smoothstep(0.15, 0.5, middle) * 0.22;
                foam *= 1 - still;
                foam += (1 - smoothstep(0, 0.09, ahead)) * lerp(1, .25, still);   // the head of the water breaks pale; a sheet creeping over a field barely does
                colour = lerp(colour, _Foam.rgb, saturate(foam) * lerp(0.26, 0.38, still));

                float alpha = saturate(lerp(_AlphaBank, _AlphaMid, smoothstep(0, 0.55, middle)) + fresnel * 0.2 + foam * 0.5);
                alpha *= smoothstep(0, 0.1, ahead);   // thin at the very edge, so it wets the ground instead of ending in a line
                colour = MixFog(colour, i.fogCoord);
                return half4(colour, alpha);
            }
            ENDHLSL
        }
    }
    FallBack Off
}
