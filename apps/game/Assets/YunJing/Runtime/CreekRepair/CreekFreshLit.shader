// Work pack B-56h: restore_channel reuses the B02 and B07 stones and shows them as newly laid with one parameter.
// _Fresh 0 looks like URP Lit with the same maps; 1 is paler stone with the moss gone. Also stands in for Qingxi/StandardVC under URP.
Shader "YunJing/CreekFreshLit"
{
    Properties
    {
        [MainTexture] _BaseMap("Base Map", 2D) = "white" {}
        [MainColor] _BaseColor("Base Color", Color) = (1, 1, 1, 1)
        [Normal] _BumpMap("Normal Map", 2D) = "bump" {}
        _Smoothness("Smoothness", Range(0, 1)) = .15
        _Fresh("Fresh", Range(0, 1)) = 0
        [Toggle] _UseVC("Use Vertex Color", Float) = 0
        _VCAmount("Vertex Color Amount", Range(0, 1)) = 1
        [HideInInspector] _Carved("Carved by the spade", Float) = 0
        [HideInInspector] _Bounce("Light bounced in off pale walls", Float) = 0
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

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_BumpMap); SAMPLER(sampler_BumpMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST; half4 _BaseColor; half _Smoothness; half _Fresh; half _UseVC; half _VCAmount; half _Carved; half _Bounce;
            CBUFFER_END

            struct In { float4 positionOS : POSITION; float3 normalOS : NORMAL; float4 tangentOS : TANGENT; float2 uv : TEXCOORD0; float2 cut : TEXCOORD3; float4 color : COLOR; };
            struct Out { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float3 positionWS : TEXCOORD1; float3 normalWS : TEXCOORD2; float4 tangentWS : TEXCOORD3; float fog : TEXCOORD4; float2 cut : TEXCOORD5; half3 vc : COLOR; };

            Out Vert(In i)
            {
                Out o; VertexPositionInputs p = GetVertexPositionInputs(i.positionOS.xyz); VertexNormalInputs n = GetVertexNormalInputs(i.normalOS, i.tangentOS);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS; o.normalWS = n.normalWS; o.tangentWS = float4(n.tangentWS, i.tangentOS.w * GetOddNegativeScale());
                o.cut = i.cut * _Carved; o.uv = TRANSFORM_TEX(i.uv, _BaseMap); o.fog = ComputeFogFactor(p.positionCS.z); o.vc = lerp(half3(1, 1, 1), SRGBToLinear(i.color.rgb), _UseVC * _VCAmount); return o;
            }

            half4 Frag(Out i) : SV_Target
            {
                half3 c = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * _BaseColor.rgb * i.vc;   // the waterworks pieces bake crevice shade into vertex colour
                half moss = saturate((c.g - max(c.r, c.b)) * 10);                     // green over the warm stone is moss
                half grey = dot(c, half3(.3, .59, .11));
                half3 stone = lerp(c, grey * half3(1.05, 1, .9), moss);
                c = lerp(c, saturate(stone * 1.1 + .025), _Fresh);

                // CarveAt: x is how deep the spade cut here, y how far water has seeped in. Anything else has neither.
                float bed = i.positionWS.y * 46 + sin(i.positionWS.x * 6.1 + i.positionWS.z * 4.3) * .9 + sin(i.positionWS.x * 17 - i.positionWS.z * 11) * .25;
                half3 layer = lerp(half3(.92, .89, .86), half3(1.04, 1.01, .97), smoothstep(-.35, .4, sin(bed))) * lerp(.96, 1, smoothstep(.02, .22, abs(sin(bed * 1.37 + 1.1))));
                c *= lerp(half3(1, 1, 1), layer, i.cut.x);
                c *= lerp(half3(1, 1, 1), half3(.72, .76, .74), i.cut.y);

                half3 t = UnpackNormal(SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, i.uv));
                half3 bitan = cross(i.normalWS, i.tangentWS.xyz) * i.tangentWS.w;
                InputData d = (InputData)0;
                d.positionWS = i.positionWS; d.positionCS = i.positionCS;
                d.normalWS = NormalizeNormalPerPixel(lerp(TransformTangentToWorld(t, half3x3(i.tangentWS.xyz, bitan, i.normalWS)), i.normalWS, i.cut.y * .85));
                d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                d.shadowCoord = TransformWorldToShadowCoord(i.positionWS); d.fogCoord = i.fog; d.bakedGI = SampleSH(d.normalWS);
                d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS); d.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = c; s.smoothness = lerp(_Smoothness * (1 - _Fresh * .5), .36, i.cut.y); s.occlusion = 1; s.alpha = 1; s.emission = c * _Bounce * (1 - .92 * GetMainLight(d.shadowCoord).shadowAttenuation) * (.3 + 1.5 * pow(saturate(dot(d.normalWS, normalize(half3(.45, .6, -.65)))), 2));   // bounced light still comes from somewhere: furrows have to read in the shade s.normalTS = t;
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
