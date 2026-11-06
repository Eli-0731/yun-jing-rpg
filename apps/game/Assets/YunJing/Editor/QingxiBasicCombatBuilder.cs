using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using YunJing.BasicCombat;

namespace YunJing.Editor
{
    // Basic combat feel-test scene (Johnnnny0823, 11/03 package A §1): the novice player with QingxiBasicCombat, the A12 vine dummy
    // that strikes back, the mountain rabbit and the sick boar as plain targets. Does not touch the main scene, QingxiFirstPerson or the
    // rabbit / boar encounter rules.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicCombatBuilder.Generate
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiBasicCombatBuilder.BuildWindows
    public static class QingxiBasicCombatBuilder
    {
        const string Scene = "Assets/YunJing/Generated/QingxiBasicCombatTest.unity";
        const string Models = "Assets/YunJing/Generated/BasicCombatTest";

        [MenuItem("Yun Jing/Generate basic combat test scene")]
        public static void Generate()
        {
            Debug.Log(QingxiBasicCombatSmoke.Verify());
            QingxiUrpUpgrade.EnsurePipeline();
            var settings = new SerializedObject(AssetDatabase.LoadAssetAtPath<UnityEngine.Object>("ProjectSettings/ProjectSettings.asset"));
            settings.FindProperty("activeInputHandler").intValue = 1; settings.ApplyModifiedPropertiesWithoutUndo();
            CopyModels();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var world = new GameObject("BasicCombatTestWorld").transform;
            Sun(world);
            Ground(world);

            var player = QingxiNoviceVillageBuilder.Player(world, new Vector3(0, 0, -3));
            var fp = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            fp.useDesignedHud = true;
            fp.spotNames = new[] { "手感測試場" }; fp.spotPositions = new[] { new Vector3(0, 0, -3) }; fp.spotYaws = new[] { 0f };
            var combat = player.AddComponent<QingxiBasicCombat>();
            combat.body = fp.body.transform; combat.cam = fp.cam;
            combat.debris = Debris(world);
            var touch = player.AddComponent<QingxiTouchControls>();
            touch.basicCombat = combat;

            var vine = Target(world, "A12_VineDummy", "A12_VineDummy", new Vector3(0, 0, 1.8f), 180, .38f, false);
            vine.strikesBack = true;
            vine.wobble = vine.transform.GetChild(0);
            var rabbit = Target(world, "Rabbit", "QingxiMountainRabbit_v003", new Vector3(-3.4f, 0, 3.2f), 140, .28f, true);
            Legacy(rabbit, "Rabbit_Idle", "Rabbit_Hit");
            var boar = Target(world, "BR01_ZhuoBoar", "BR01_ZhuoBoar_v001", new Vector3(3.8f, 0, 3.6f), 220, .65f, true);
            Legacy(boar, "Idle", "Paw");

            var demo = new GameObject("BasicCombatDemo").AddComponent<QingxiBasicCombatDemo>();
            demo.transform.SetParent(world, false);
            demo.combat = combat; demo.vine = vine; demo.rabbit = rabbit; demo.boar = boar;

            Physics.SyncTransforms();
            Directory.CreateDirectory(Path.GetDirectoryName(Scene));
            if (!EditorSceneManager.SaveScene(scene, Scene)) throw new IOException("Could not save " + Scene);
            AssetDatabase.SaveAssets();
            Debug.Log("QINGXI_BASIC_COMBAT_SCENE " + Scene);
        }

        // Run Generate first in its own Unity run: it switches the project to the Input System, and building in the same run would
        // use the old script layout ("script class layout is incompatible").
        public static void BuildWindows()
        {
            if (!File.Exists(Scene)) throw new FileNotFoundException("Run Generate first", Scene);
            PlayerSettings.runInBackground = true;
            var report = UnityEditor.BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = new[] { Scene },
                locationPathName = Path.GetFullPath(Path.Combine(Application.dataPath, "../Builds/BasicCombatTest/BasicCombatTest.exe")),
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            });
            Debug.Log($"QINGXI_BASIC_COMBAT_BUILD {report.summary.result} errors={report.summary.totalErrors}");
            if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded) EditorApplication.Exit(1);
        }

        static QingxiCombatTestTarget Target(Transform world, string id, string model, Vector3 at, float yaw, float radius, bool slides)
        {
            var root = new GameObject("CombatTarget_" + id);
            root.transform.SetParent(world, false);
            root.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            var pivot = new GameObject("Wobble").transform;
            pivot.SetParent(root.transform, false);
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{model}.fbx");
            if (source == null) throw new InvalidOperationException("Model missing: " + model);
            var go = (GameObject)PrefabUtility.InstantiatePrefab(source);
            go.transform.SetParent(pivot, false);
            ApplyMaterial(go, model);
            var col = root.AddComponent<CapsuleCollider>();
            col.radius = radius; col.height = 1.2f; col.center = Vector3.up * .6f;
            var t = root.AddComponent<QingxiCombatTestTarget>();
            t.id = id; t.radius = radius; t.canSlide = slides; t.wobble = pivot;
            return t;
        }

        static void Legacy(QingxiCombatTestTarget t, string idle, string hit)
        {
            var anim = t.GetComponentInChildren<Animation>();
            if (anim == null) return;
            anim.wrapMode = WrapMode.Loop;
            t.legacy = anim; t.idleClip = idle; t.hitClip = hit;
            if (anim[idle] != null) { anim.clip = anim[idle].clip; anim.playAutomatically = true; }
            if (anim[hit] != null) anim[hit].wrapMode = WrapMode.Once;
        }

        static void ApplyMaterial(GameObject go, string model)
        {
            string key = model.Replace("_v001", "");
            var baseTex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/textures/T_{key}_BaseColor.png");
            if (baseTex == null) return;   // the rabbit carries its own materials
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var m = new Material(lit) { name = "M_" + key + "_CombatTest" };
            m.SetTexture("_BaseMap", baseTex);
            var normal = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/textures/T_{key}_Normal.png");
            if (normal != null) { m.SetTexture("_BumpMap", normal); m.EnableKeyword("_NORMALMAP"); }
            m.SetFloat("_Smoothness", .25f);
            m.EnableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", Color.black);
            m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
            AssetDatabase.CreateAsset(m, $"{Models}/{m.name}.mat");
            foreach (var r in go.GetComponentsInChildren<Renderer>())
                r.sharedMaterials = Enumerable.Repeat(m, r.sharedMaterials.Length).ToArray();
        }

        static void CopyModels()
        {
            string art = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../art/exports"));
            Directory.CreateDirectory(Path.Combine(Models, "textures"));
            void Copy(string from, string to) => File.Copy(Path.Combine(art, from), Path.Combine(Models, to), true);
            Copy("qingxi-encounter-a/A12_VineDummy.fbx", "A12_VineDummy.fbx");
            foreach (var map in new[] { "BaseColor", "Normal" })
                Copy($"qingxi-encounter-a/textures/T_A12_VineDummy_{map}.png", $"textures/T_A12_VineDummy_{map}.png");
            Copy("qingxi-mountain-rabbit-v003/QingxiMountainRabbit_v003.fbx", "QingxiMountainRabbit_v003.fbx");
            Copy("zhuo-boar-a/BR01_ZhuoBoar/BR01_ZhuoBoar_v001.fbx", "BR01_ZhuoBoar_v001.fbx");
            foreach (var map in new[] { "BaseColor", "Normal" })
                Copy($"zhuo-boar-a/BR01_ZhuoBoar/textures/T_BR01_ZhuoBoar_{map}.png", $"textures/T_BR01_ZhuoBoar_{map}.png");
            AssetDatabase.Refresh();
            foreach (var tex in Directory.GetFiles(Path.Combine(Models, "textures"), "*_Normal.png"))
            {
                var ti = (TextureImporter)AssetImporter.GetAtPath(tex.Replace('\\', '/'));
                ti.textureType = TextureImporterType.NormalMap; ti.SaveAndReimport();
            }
            foreach (var (model, legacy) in new[] { ("A12_VineDummy", false), ("QingxiMountainRabbit_v003", true), ("BR01_ZhuoBoar_v001", true) })
            {
                var mi = (ModelImporter)AssetImporter.GetAtPath($"{Models}/{model}.fbx");
                mi.globalScale = 1; mi.useFileScale = true;
                mi.animationType = legacy ? ModelImporterAnimationType.Legacy : ModelImporterAnimationType.None;
                mi.importAnimation = legacy;
                mi.SaveAndReimport();
                if (legacy)
                {
                    var takes = mi.defaultClipAnimations;
                    foreach (var take in takes)
                    {
                        int bar = take.name.LastIndexOf('|');
                        take.name = bar >= 0 ? take.name.Substring(bar + 1) : take.name;
                        take.loopTime = !take.name.Contains("Hit") && take.name != "Paw";
                        take.wrapMode = take.loopTime ? WrapMode.Loop : WrapMode.Once;
                    }
                    mi.clipAnimations = takes;
                    mi.SaveAndReimport();
                }
            }
        }

        static ParticleSystem Debris(Transform world)
        {
            var go = new GameObject("CombatDebris");
            go.transform.SetParent(world, false);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.playOnAwake = false; main.loop = false;
            main.startLifetime = new ParticleSystem.MinMaxCurve(.35f, .7f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(1.5f, 4.5f);
            main.startSize = new ParticleSystem.MinMaxCurve(.025f, .07f);
            main.startColor = new ParticleSystem.MinMaxGradient(new Color(.55f, .42f, .26f), new Color(.85f, .74f, .5f));
            main.gravityModifier = 1.4f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.useUnscaledTime = true;
            main.maxParticles = 200;
            var em = ps.emission; em.rateOverTime = 0;
            var shape = ps.shape; shape.shapeType = ParticleSystemShapeType.Sphere; shape.radius = .08f;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.Mesh;
            r.mesh = Resources.GetBuiltinResource<Mesh>("Cube.fbx");
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "M_CombatDebris" };
            m.SetColor("_BaseColor", Color.white);
            AssetDatabase.CreateAsset(m, $"{Models}/M_CombatDebris.mat");
            r.sharedMaterial = m;
            return ps;
        }

        static void Sun(Transform world)
        {
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.transform.SetParent(world, false);
            sun.type = LightType.Directional; sun.intensity = 1.6f; sun.color = new Color(1f, .9f, .74f);
            sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(32, -35, 0);
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.62f, .7f, .82f);
            RenderSettings.ambientEquatorColor = new Color(.6f, .58f, .5f);
            RenderSettings.ambientGroundColor = new Color(.3f, .28f, .22f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = new Color(.91f, .89f, .85f); RenderSettings.fogStartDistance = 25; RenderSettings.fogEndDistance = 90;
        }

        static void Ground(Transform world)
        {
            var g = GameObject.CreatePrimitive(PrimitiveType.Cube);
            g.name = "PracticeGround_24x24"; g.transform.SetParent(world, false);
            g.transform.localScale = new Vector3(24, .2f, 24); g.transform.localPosition = new Vector3(0, -.1f, 2);
            var m = new Material(Shader.Find("Universal Render Pipeline/Lit")) { name = "M_CombatTestGround" };
            m.SetColor("_BaseColor", new Color(.56f, .58f, .4f)); m.SetFloat("_Smoothness", .05f);
            Directory.CreateDirectory(Models);
            AssetDatabase.CreateAsset(m, $"{Models}/M_CombatTestGround.mat");
            g.GetComponent<Renderer>().sharedMaterial = m;
        }
    }
}
