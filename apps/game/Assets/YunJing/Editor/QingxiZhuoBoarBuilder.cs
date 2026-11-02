using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // The day 3 boar's test scene: 20 x 20 m flat ground, three pines on D3_BoarTree_01..03, two stone slot boxes, the encounter on
    // D3_BoarEncounter. Copies BR01 and BR02 from art/exports/zhuo-boar-a into the git-ignored Generated folder. Does not touch the
    // main scene: the core team puts the D3_BoarEncounter object (or PlaceEncounter) into D3 and calls BeginFromScript.
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiZhuoBoarBuilder.Generate
    //   Unity -batchmode -quit -projectPath apps/game -executeMethod YunJing.Editor.QingxiZhuoBoarBuilder.BuildWindows
    public static class QingxiZhuoBoarBuilder
    {
        const string Scene = "Assets/YunJing/Generated/QingxiZhuoBoarTest.unity";
        const string Models = "Assets/YunJing/Generated/ZhuoBoarA";
        const string Boar = "BR01_ZhuoBoar", PineA = "BR02_YoungPine_A", PineB = "BR02_YoungPine_B";
        const string FxMaterial = "Assets/YunJing/Resources/QingxiZhuoBoar/ZhuoFx.mat";
        static readonly string[] Clips = { "Idle", "Paw", "Charge", "Daze", "Cleanse", "Flee" };

        [MenuItem("Yun Jing/Generate day 3 boar test scene")]
        public static void Generate()
        {
            Debug.Log(QingxiZhuoBoarSmoke.Verify());
            QingxiUrpUpgrade.EnsurePipeline();
            var settings = new SerializedObject(AssetDatabase.LoadAssetAtPath<UnityEngine.Object>("ProjectSettings/ProjectSettings.asset"));
            settings.FindProperty("activeInputHandler").intValue = 1; settings.ApplyModifiedPropertiesWithoutUndo();

            CopyExports();
            EnsureFxMaterial();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var world = new GameObject("BoarTestWorld").transform;
            Light(world);
            Ground(world);
            var player = QingxiNoviceVillageBuilder.Player(world, new Vector3(0, 0, -6));
            var fp = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            fp.useDesignedHud = true;
            fp.spotNames = new[] { "測試場" }; fp.spotPositions = new[] { new Vector3(0, 0, -6) }; fp.spotYaws = new[] { 0f };
            player.AddComponent<QingxiTouchControls>();

            var pines = new (string slot, string model, Vector3 at, float yaw)[] {
                ("D3_BoarTree_01", PineA, new Vector3(-4.5f, 0, 1.5f), 20),
                ("D3_BoarTree_02", PineB, new Vector3(4.2f, 0, 2.5f), 140),
                ("D3_BoarTree_03", PineA, new Vector3(.5f, 0, -3.5f), 250),
            };
            foreach (var p in pines) Pine(world, p.slot, p.model, p.at, p.yaw);
            Stone(world, "BoarStone_Slot_01", new Vector3(6, .5f, -5.5f), new Vector3(1.6f, 1, 1.4f));
            Stone(world, "BoarStone_Slot_02", new Vector3(-6.5f, .45f, -4), new Vector3(1.4f, .9f, 1.4f));
            PlaceEncounter(world, new Vector3(0, 0, 7), 180, new Vector2(-9.6f, -9.6f), new Vector2(9.6f, 9.6f), true);

            Physics.SyncTransforms();
            Directory.CreateDirectory(Path.GetDirectoryName(Scene));
            if (!EditorSceneManager.SaveScene(scene, Scene)) throw new IOException("Could not save " + Scene);
            AssetDatabase.SaveAssets();
            Debug.Log("QINGXI_ZHUO_BOAR_SCENE " + Scene);
        }

        public static void BuildWindows()
        {
            if (!File.Exists(Scene)) throw new InvalidOperationException("Generate the boar test scene in a previous Editor process.");
            QingxiUrpUpgrade.EnsurePipeline();
            PlayerSettings.SplashScreen.show = false;
            PlayerSettings.runInBackground = true;   // the review hooks must keep playing behind other windows
            string path = "../../artifacts/windows-zhuo-boar/YunJingZhuoBoar.exe";
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes = new[] { Scene }, target = BuildTarget.StandaloneWindows64, locationPathName = path, options = BuildOptions.None });
            if (report.summary.result != BuildResult.Succeeded) throw new InvalidOperationException("Build failed: " + report.summary.totalErrors + " errors");
            Debug.Log("QINGXI_ZHUO_BOAR_BUILD " + path);
        }

        // The D3_BoarEncounter slot with BR01 on it. Empty bounds mean no limit, for a place with its own terrain.
        public static QingxiZhuoBoarEncounter PlaceEncounter(Transform parent, Vector3 at, float yaw, Vector2 boundsMin, Vector2 boundsMax, bool startOnNotice)
        {
            var slot = new GameObject("D3_BoarEncounter");
            slot.transform.SetParent(parent, false);
            slot.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            var e = slot.AddComponent<QingxiZhuoBoarEncounter>();
            e.startOnNotice = startOnNotice;
            e.useBounds = boundsMax != boundsMin; e.boundsMin = boundsMin; e.boundsMax = boundsMax;

            var holder = new GameObject("BR01_Holder").transform;
            holder.SetParent(slot.transform, false);
            var boar = (GameObject)PrefabUtility.InstantiatePrefab(LoadModel(Boar));
            boar.name = Boar + "_Model";
            boar.transform.SetParent(holder, false);
            // The model's front is Blender's -Y, which the FBX axes bring in along Unity's +Z.
            var material = LoadMaterial(Boar, 0);
            var levels = new[] { Boar, Boar + "_LOD1", Boar + "_LOD2" };
            var lods = new LOD[levels.Length];
            float[] heights = { .42f, .16f, .03f };
            for (int i = 0; i < levels.Length; i++)
            {
                var part = FindDeep(boar.transform, levels[i]);
                var r = part.GetComponent<Renderer>();
                r.sharedMaterial = material;
                if (r is SkinnedMeshRenderer sk) { sk.updateWhenOffscreen = false; sk.localBounds = new Bounds(new Vector3(0, .5f, 0), new Vector3(1.6f, 1.2f, 2f)); }
                lods[i] = new LOD(heights[i], new[] { r });
            }
            boar.AddComponent<LODGroup>().SetLODs(lods);
            var hull = FindDeep(boar.transform, Boar + "_Collision");
            if (hull != null) { foreach (var r in hull.GetComponents<Renderer>()) UnityEngine.Object.DestroyImmediate(r); }
            e.boarModel = holder;
            e.clips = boar.GetComponent<Animation>();
            if (e.clips == null) Debug.LogWarning("BR01 has no Animation component");
            return e;
        }

        static void Pine(Transform parent, string slot, string model, Vector3 at, float yaw)
        {
            var go = new GameObject(slot);
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(at, Quaternion.Euler(0, yaw, 0));
            var tree = (GameObject)PrefabUtility.InstantiatePrefab(LoadModel(model));
            tree.name = model + "_Model";
            tree.transform.SetParent(go.transform, false);
            var material = LoadMaterial(model, 1);
            var levels = new[] { model, model + "_LOD1", model + "_LOD2" };
            var lods = new LOD[levels.Length];
            float[] heights = { .4f, .14f, .03f };
            for (int i = 0; i < levels.Length; i++)
            {
                var part = FindDeep(tree.transform, levels[i]);
                var r = part.GetComponent<Renderer>();
                r.sharedMaterial = material;
                lods[i] = new LOD(heights[i], new[] { r });
            }
            tree.AddComponent<LODGroup>().SetLODs(lods);
            var hull = FindDeep(tree.transform, model + "_Collision");
            var mesh = hull.GetComponent<MeshFilter>().sharedMesh;
            UnityEngine.Object.DestroyImmediate(hull.GetComponent<Renderer>());
            UnityEngine.Object.DestroyImmediate(hull.GetComponent<MeshFilter>());
            var collider = hull.gameObject.AddComponent<MeshCollider>();
            collider.sharedMesh = mesh; collider.convex = true;
            go.AddComponent<BoarObstacle>().leanDegrees = 8;
        }

        static void Stone(Transform parent, string name, Vector3 at, Vector3 size)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name; go.transform.SetParent(parent, false); go.transform.position = at; go.transform.localScale = size;
            go.GetComponent<Renderer>().sharedMaterial = Plain("SlotStone", new Color(.54f, .52f, .47f));
            go.AddComponent<BoarObstacle>();
        }

        static void Ground(Transform parent)
        {
            var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
            ground.name = "Ground_20x20"; ground.transform.SetParent(parent, false);
            ground.transform.position = new Vector3(0, -.5f, 0); ground.transform.localScale = new Vector3(20, 1, 20);
            ground.GetComponent<Renderer>().sharedMaterial = Plain("SlotGround", new Color(.36f, .42f, .24f));
            var beyond = GameObject.CreatePrimitive(PrimitiveType.Cube);
            beyond.name = "BeyondGround"; beyond.transform.SetParent(parent, false);
            beyond.transform.position = new Vector3(0, -.56f, 0); beyond.transform.localScale = new Vector3(200, 1, 200);
            beyond.GetComponent<Renderer>().sharedMaterial = Plain("SlotBeyond", new Color(.3f, .36f, .22f));
            foreach (var (x, z, w, d) in new[] { (0f, 10.2f, 21f, .4f), (0f, -10.2f, 21f, .4f), (10.2f, 0f, .4f, 21f), (-10.2f, 0f, .4f, 21f) })
            {
                var wall = new GameObject("Fence"); wall.transform.SetParent(parent, false);
                wall.transform.position = new Vector3(x, 1, z);
                wall.AddComponent<BoxCollider>().size = new Vector3(w, 3, d);
            }
        }

        static void Light(Transform parent)
        {
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.transform.SetParent(parent, false);
            sun.type = LightType.Directional; sun.color = new Color(1, .86f, .66f); sun.intensity = 1.3f; sun.shadows = LightShadows.Soft;
            sun.transform.rotation = Quaternion.Euler(30, -38, 0);
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.56f, .62f, .74f); RenderSettings.ambientEquatorColor = new Color(.5f, .52f, .48f); RenderSettings.ambientGroundColor = new Color(.28f, .26f, .24f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogColor = new Color(.82f, .84f, .82f);
            RenderSettings.fogStartDistance = 30; RenderSettings.fogEndDistance = 110;
            var path = Models + "/Sky.mat";
            var sky = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (sky == null) { sky = new Material(Shader.Find("Skybox/Procedural")); AssetDatabase.CreateAsset(sky, path); }
            sky.SetColor("_SkyTint", new Color(.55f, .68f, .86f)); sky.SetColor("_GroundColor", new Color(.82f, .84f, .82f)); sky.SetFloat("_AtmosphereThickness", .85f); sky.SetFloat("_Exposure", 1.15f);
            RenderSettings.skybox = sky;
        }

        static void EnsureFxMaterial()
        {
            if (AssetDatabase.LoadAssetAtPath<Material>(FxMaterial) != null) return;
            var shader = Shader.Find("YunJing/QingxiZhuoFx");
            if (shader == null) throw new InvalidOperationException("YunJing/QingxiZhuoFx did not compile");
            AssetDatabase.CreateAsset(new Material(shader), FxMaterial);
        }

        static Material Plain(string name, Color colour)
        {
            var path = Models + "/" + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(Shader.Find("Universal Render Pipeline/Lit")); AssetDatabase.CreateAsset(m, path); }
            m.SetColor("_BaseColor", colour); m.SetFloat("_Smoothness", .05f);
            return m;
        }

        static Material LoadMaterial(string key, int kind)
        {
            var path = $"{Models}/{key}/M_{key}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                var shader = Shader.Find("YunJing/QingxiZhuoBoar");
                if (shader == null) throw new InvalidOperationException("YunJing/QingxiZhuoBoar did not compile");
                m = new Material(shader);
                AssetDatabase.CreateAsset(m, path);
            }
            m.SetTexture("_BaseMap", Tex(key, "BaseColor")); m.SetTexture("_NormalMap", Tex(key, "Normal")); m.SetTexture("_OrmMap", Tex(key, "ORM")); m.SetTexture("_MaskMap", Tex(key, "Mask"));
            if (kind == 0) m.SetTexture("_FurMap", Tex(key, "Fur"));
            if (kind == 1) { m.SetFloat("_Strength", .05f); m.SetFloat("_Flutter", .012f); m.SetFloat("_Height", 5); m.SetFloat("_Wrap", .45f); m.SetFloat("_Zhuo", 0); }
            EditorUtility.SetDirty(m);
            return m;
        }

        static Texture2D Tex(string key, string map) => AssetDatabase.LoadAssetAtPath<Texture2D>($"{Models}/{key}/textures/T_{key}_{map}.png");

        static GameObject LoadModel(string key) => AssetDatabase.LoadAssetAtPath<GameObject>($"{Models}/{key}/{key}_v001.fbx");

        static Transform FindDeep(Transform root, string name)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t;
            return null;
        }

        static void CopyExports()
        {
            string source = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../art/exports/zhuo-boar-a"));
            foreach (var key in new[] { Boar, PineA, PineB })
            {
                string from = Path.Combine(source, key), to = Path.Combine(Models, key);
                Directory.CreateDirectory(Path.Combine(to, "textures"));
                File.Copy(Path.Combine(from, $"{key}_v001.fbx"), Path.Combine(to, $"{key}_v001.fbx"), true);
                foreach (var f in Directory.GetFiles(Path.Combine(from, "textures"), "*.png")) File.Copy(f, Path.Combine(to, "textures", Path.GetFileName(f)), true);
            }
            AssetDatabase.Refresh();
            foreach (var key in new[] { Boar, PineA, PineB })
            {
                foreach (var (map, linear, normal) in new[] { ("BaseColor", false, false), ("ORM", true, false), ("Normal", true, true), ("Mask", true, false) })
                {
                    var ti = (TextureImporter)AssetImporter.GetAtPath($"{Models}/{key}/textures/T_{key}_{map}.png");
                    ti.sRGBTexture = !linear; ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                    ti.alphaSource = TextureImporterAlphaSource.None; ti.maxTextureSize = 2048;
                    ti.SaveAndReimport();
                }
                if (key == Boar)
                {
                    var fur = (TextureImporter)AssetImporter.GetAtPath($"{Models}/{key}/textures/T_{key}_Fur.png");
                    fur.sRGBTexture = false; fur.alphaSource = TextureImporterAlphaSource.FromInput; fur.alphaIsTransparency = false;
                    fur.mipmapEnabled = true; fur.mipMapsPreserveCoverage = true; fur.alphaTestReferenceValue = .5f;
                    fur.wrapMode = TextureWrapMode.Clamp; fur.maxTextureSize = 1024;
                    fur.SaveAndReimport();
                }
                var mi = (ModelImporter)AssetImporter.GetAtPath($"{Models}/{key}/{key}_v001.fbx");
                mi.globalScale = 1; mi.useFileScale = true;
                mi.materialImportMode = ModelImporterMaterialImportMode.None;
                mi.importNormals = ModelImporterNormals.Import;
                mi.importTangents = ModelImporterTangents.CalculateMikk;
                mi.isReadable = false;
                if (key == Boar)
                {
                    mi.animationType = ModelImporterAnimationType.Legacy;
                    mi.importAnimation = true;
                    mi.SaveAndReimport();
                    var takes = mi.defaultClipAnimations;
                    foreach (var take in takes)
                    {
                        int bar = take.name.LastIndexOf('|');
                        take.name = bar >= 0 ? take.name.Substring(bar + 1) : take.name;
                        take.wrapMode = take.name == "Cleanse" ? WrapMode.ClampForever : WrapMode.Loop;
                        take.loopTime = take.name != "Cleanse";
                    }
                    mi.clipAnimations = takes;
                    foreach (var clip in Clips)
                        if (Array.Find(takes, t => t.name == clip) == null) throw new InvalidDataException("BR01 FBX is missing the clip " + clip + " (has " + string.Join(", ", Array.ConvertAll(takes, t => t.name)) + ")");
                }
                else mi.animationType = ModelImporterAnimationType.None;
                mi.SaveAndReimport();
            }
            AssetDatabase.Refresh();
        }
    }
}
