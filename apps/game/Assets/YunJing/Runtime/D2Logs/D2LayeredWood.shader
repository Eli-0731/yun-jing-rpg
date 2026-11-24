// D2 倒木（B 包 DR08 朽木起）：六層手繪平鋪貼圖（樹皮、苔、褐腐木、撕裂纖維、樹洞內壁、土）用頂點權重混合。
//   UV0：公尺（每層各自乘 _Tiles 的重複次數）；頂點色 RGBA：苔、褐腐木、纖維、內壁的權重；UV1.x：土的權重、UV1.y：AO（1 = 不遮）。
//   樹皮 = 1 − 其他權重總和。交界用各層貼圖的明暗當高度做高度混合：苔會沿樹皮的溝爬進去、不是一條模糊的漸層。
// 貼圖由 art/source/d2-logs-b/tex_dr08.py 從 Codex 照 D2 設定圖畫的原圖做出來（每張 1024，匯入規則照專案上限）。
Shader "YunJing/D2LayeredWood"
{
    Properties
    {
        _BarkMap("Bark", 2D) = "white" {}
        [Normal] _BarkNrm("Bark Normal", 2D) = "bump" {}
        _MossMap("Moss", 2D) = "white" {}
        [Normal] _MossNrm("Moss Normal", 2D) = "bump" {}
        _RotMap("Brown rot", 2D) = "white" {}
        [Normal] _RotNrm("Brown rot Normal", 2D) = "bump" {}
        _FibreMap("Torn fibre", 2D) = "white" {}
        [Normal] _FibreNrm("Torn fibre Normal", 2D) = "bump" {}
        _InnerMap("Hollow inner", 2D) = "white" {}
        [Normal] _InnerNrm("Hollow inner Normal", 2D) = "bump" {}
        _SoilMap("Soil", 2D) = "white" {}
        [Normal] _SoilNrm("Soil Normal", 2D) = "bump" {}
        _TilesA("Repeats per metre: bark, moss, rot, fibre", Vector) = (1, 2, 2, 1)
        _TilesB("Repeats per metre: inner, soil", Vector) = (1, 1, 0, 0)
        _Smooth("Smoothness: bark, moss, rot, fibre", Vector) = (.10, .04, .06, .10)
        _SmoothB("Smoothness: inner, soil", Vector) = (.22, .08, 0, 0)
        _BlendSharp("Height blend sharpness", Range(.02, 1)) = .18
        _AOStrength("Vertex AO strength", Range(0, 1)) = 1
        _NormalStrength("Normal strength", Range(0, 2)) = 1
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
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_BarkMap); TEXTURE2D(_BarkNrm); TEXTURE2D(_MossMap); TEXTURE2D(_MossNrm);
            TEXTURE2D(_RotMap); TEXTURE2D(_RotNrm); TEXTURE2D(_FibreMap); TEXTURE2D(_FibreNrm);
            TEXTURE2D(_InnerMap); TEXTURE2D(_InnerNrm); TEXTURE2D(_SoilMap); TEXTURE2D(_SoilNrm);
            SAMPLER(sampler_BarkMap);                     // 一個取樣器給全部（手機上取樣器槽位有限）
            CBUFFER_START(UnityPerMaterial)
                float4 _TilesA; float4 _TilesB; half4 _Smooth; half4 _SmoothB; half _BlendSharp; half _AOStrength; half _NormalStrength;
            CBUFFER_END

            struct In { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float2 extra : TEXCOORD1; float4 color : COLOR; };
            struct Out { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; float3 normalWS : TEXCOORD2; float4 tangentWS : TEXCOORD3; float fog : TEXCOORD4; float2 extra : TEXCOORD5; half4 w : COLOR; };

            Out Vert(In i)
            {
                Out o; VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz); VertexNormalInputs n = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS; o.normalWS = n.normalWS; o.tangentWS = float4(n.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.uv = i.uv; o.extra = i.extra; o.w = i.color; o.fog = ComputeFogFactor(p.positionCS.z); return o;
            }

            half Lum(half3 c) { return dot(c, half3(.30, .59, .11)); }

            half4 Frag(Out i) : SV_Target
            {
                float2 uB = i.uv * _TilesA.x, uM = i.uv * _TilesA.y, uR = i.uv * _TilesA.z, uF = i.uv * _TilesA.w, uI = i.uv * _TilesB.x, uS = i.uv * _TilesB.y;
                half3 cB = SAMPLE_TEXTURE2D(_BarkMap, sampler_BarkMap, uB).rgb;
                half3 cM = SAMPLE_TEXTURE2D(_MossMap, sampler_BarkMap, uM).rgb;
                half3 cR = SAMPLE_TEXTURE2D(_RotMap, sampler_BarkMap, uR).rgb;
                half3 cF = SAMPLE_TEXTURE2D(_FibreMap, sampler_BarkMap, uF).rgb;
                half3 cI = SAMPLE_TEXTURE2D(_InnerMap, sampler_BarkMap, uI).rgb;
                half3 cS = SAMPLE_TEXTURE2D(_SoilMap, sampler_BarkMap, uS).rgb;

                // 權重：苔、腐木、纖維、內壁、土來自頂點，樹皮是剩下的；高度混合（亮的地方＝凸的地方先蓋上去）
                half wM = i.w.r, wR = i.w.g, wF = i.w.b, wI = i.w.a, wS = i.extra.x;
                half wB = saturate(1 - wM - wR - wF - wI - wS);
                half hB = wB + Lum(cB), hM = wM + Lum(cM) * 1.4, hR = wR + Lum(cR), hF = wF + Lum(cF), hI = wI + Lum(cI), hS = wS + Lum(cS);
                half top = max(max(max(hB, hM), max(hR, hF)), max(hI, hS)) - _BlendSharp;
                half bB = max(hB - top, 0) * step(.001, wB), bM = max(hM - top, 0) * step(.001, wM), bR = max(hR - top, 0) * step(.001, wR);
                half bF = max(hF - top, 0) * step(.001, wF), bI = max(hI - top, 0) * step(.001, wI), bS = max(hS - top, 0) * step(.001, wS);
                half sum = max(bB + bM + bR + bF + bI + bS, 1e-4);
                bB /= sum; bM /= sum; bR /= sum; bF /= sum; bI /= sum; bS /= sum;

                half3 albedo = cB * bB + cM * bM + cR * bR + cF * bF + cI * bI + cS * bS;
                half3 t = UnpackNormal(SAMPLE_TEXTURE2D(_BarkNrm, sampler_BarkMap, uB)) * bB
                        + UnpackNormal(SAMPLE_TEXTURE2D(_MossNrm, sampler_BarkMap, uM)) * bM
                        + UnpackNormal(SAMPLE_TEXTURE2D(_RotNrm, sampler_BarkMap, uR)) * bR
                        + UnpackNormal(SAMPLE_TEXTURE2D(_FibreNrm, sampler_BarkMap, uF)) * bF
                        + UnpackNormal(SAMPLE_TEXTURE2D(_InnerNrm, sampler_BarkMap, uI)) * bI
                        + UnpackNormal(SAMPLE_TEXTURE2D(_SoilNrm, sampler_BarkMap, uS)) * bS;
                t.xy *= _NormalStrength; t = normalize(t);
                half smooth = _Smooth.x * bB + _Smooth.y * bM + _Smooth.z * bR + _Smooth.w * bF + _SmoothB.x * bI + _SmoothB.y * bS;
                half ao = lerp(1, i.extra.y, _AOStrength);

                half3 bitan = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;
                InputData d = (InputData)0;
                d.positionWS = i.positionWS; d.positionCS = i.positionCS;
                d.normalWS = NormalizeNormalPerPixel(TransformTangentToWorld(t, half3x3(i.tangentWS.xyz, bitan, i.normalWS)));
                d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                d.shadowCoord = TransformWorldToShadowCoord(i.positionWS); d.fogCoord = i.fog; d.bakedGI = SampleSH(d.normalWS);
                d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS); d.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = albedo * lerp(1, ao, .5); s.smoothness = smooth; s.occlusion = ao; s.alpha = 1; s.normalTS = t;
                half4 color = UniversalFragmentPBR(d, s);
                color.rgb = MixFog(color.rgb, d.fogCoord);
                return color;
            }
            ENDHLSL
        }
        UsePass "Universal Render Pipeline/Lit/ShadowCaster"
        UsePass "Universal Render Pipeline/Lit/DepthOnly"
        UsePass "Universal Render Pipeline/Lit/DepthNormals"
    }
    FallBack "Universal Render Pipeline/Lit"
}
