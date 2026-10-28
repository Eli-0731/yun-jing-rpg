using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    // Places the 2026-10-29 collaborator deliveries into the Qingxi novice village:
    // A (Johnnnny0823) forest rabbit encounter A01-A12, B (joshsu54) alchemy corner B01-B12 with a door
    // into his AlchemyRoom scene, C (Eli-0731) return sorting corner C01-C08. Source meshes are copied
    // from art/exports unchanged; layouts come from Assets/YunJing/Data/QingxiAbcZones.json.
    public static class QingxiCollaboratorZonesBuilder
    {
        public const string DataPath = "Assets/YunJing/Data/QingxiAbcZones.json";
        const string ForestModels = "Assets/YunJing/Models/ForestEncounterA";
        const string RabbitModels = "Assets/YunJing/Models/ForestEncounterA/Rabbit";
        const string AlchemyModels = "Assets/YunJing/Models/AlchemyB";   // same copy target as AlchemyRoomBuilder
        public const string ReturnModels = "Assets/YunJing/Models/VillageReturnC";
        public const string SignModels = "Assets/YunJing/Models/VillageSignsC";
        const string TrainingModels = "Assets/YunJing/Models/TrainingYardA";
        const string MaterialFolder = "Assets/QingxiWorld/Generated/Materials/Collaborators";
        static string Repo => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));

        public sealed class Result
        {
            public Transform forest, alchemy, ret, alchemyDoor, returnTable;
            public QingxiForestEncounter encounter;
            public readonly List<string> report = new List<string>();
            public int models;
        }

        [Serializable] class ModelInfo { public float[] dimensions_m; }

        // Novice village: the same three kits at authored positions on flat ground, no placement search.
        public static Result PlaceAt(GameObject player, Vector3 forest, float forestYaw, Vector3 alchemy, float alchemyYaw, Vector3 ret, float retYaw)
        {
            var dataAsset = AssetDatabase.LoadAssetAtPath<TextAsset>(DataPath);
            if (dataAsset == null) throw new InvalidOperationException("Missing " + DataPath + "; run node tools/qingxi-main-scene/build-data.mjs");
            var data = QingxiAbcZoneData.Parse(dataAsset.text);
            CopyKits(data);
            QingxiForestEncounterSmoke.Verify(data);
            QingxiReturnSortingSmoke.Verify();
            Directory.CreateDirectory(MaterialFolder);
            Physics.SyncTransforms();
            var result = new Result();
            result.forest = BuildForest(data, new Anchor { position = forest, yaw = forestYaw }, player, result);
            result.alchemy = BuildAlchemy(data, new Anchor { position = alchemy, yaw = alchemyYaw }, result);
            result.ret = BuildReturn(data, new Anchor { position = ret, yaw = retYaw }, result);
            return result;
        }

        // Johnnnny0823's training-yard kit (art/exports/qingxi-training-yard-v1), same import rules as A.
        public static GameObject PlaceTrainingProp(string key, Transform parent, Vector3 local, float yaw, Result result)
        {
            var model = Kit(TrainingModels, key, key + " - by Johnnnny0823", parent, local, yaw,
                Path.Combine(Repo, "art/exports/qingxi-training-yard-v1", key + "_model_info.json"), result);
            Solid(model);
            return model;
        }

        // Eli-0731's GLB-only deliveries converted by tools/art/import_qingxi_return_c_to_unity.py.
        public static GameObject PlaceConverted(string folder, string id, Transform parent, Vector3 local, float yaw, Result result)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{folder}/{id}.fbx");
            if (source == null) throw new InvalidOperationException($"Missing converted model {folder}/{id}.fbx");
            var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
            model.name = id + " - by Eli-0731";
            model.transform.SetParent(parent, false);
            model.transform.localPosition = local;
            model.transform.localRotation = Quaternion.Euler(0, yaw, 0);
            foreach (var r in model.GetComponentsInChildren<Renderer>())
                r.sharedMaterials = r.sharedMaterials.Select(m => ReturnMaterial(folder, id, m)).ToArray();
            result.models++;
            return model;
        }


        struct Anchor { public Vector3 position; public float yaw; }

        // Ground under a zone-local point when a NavMesh is loaded; the flat novice village has none (0).
        static float LocalGround(Transform root, float x, float z)
        {
            var world = root.TransformPoint(new Vector3(x, 0, z));
            if (!NavMesh.SamplePosition(world, out var nav, 3f, NavMesh.AllAreas)) return 0;
            var hits = Physics.RaycastAll(nav.position + Vector3.up * .6f, Vector3.down, 1.6f, ~0, QueryTriggerInteraction.Ignore)
                .Where(h => !h.collider.transform.IsChildOf(root)).OrderBy(h => h.distance).ToArray();
            return (hits.Length > 0 ? hits[0].point.y : nav.position.y) - root.position.y;
        }

        static Transform Root(string name, Anchor anchor)
        {
            var root = new GameObject(name).transform;
            root.SetPositionAndRotation(anchor.position, Quaternion.Euler(0, anchor.yaw, 0));
            return root;
        }

        // ------------------------------------------------------------------ A: forest encounter
        static Transform BuildForest(QingxiAbcZoneData data, Anchor anchor, GameObject player, Result result)
        {
            var root = Root("CollaboratorZone_A_ForestEncounter (Johnnnny0823)", anchor);
            GameObject intact = null, worn = null;
            foreach (var item in data.forest.layout)
            {
                var model = Kit(ForestModels, item.id, item.id, root, new Vector3(item.x, item.y + LocalGround(root, item.x, item.z), item.z), item.rot * Mathf.Rad2Deg,
                    Path.Combine(Repo, "art/exports/qingxi-encounter-a", item.id + "_model_info.json"), result);
                foreach (var mf in Lod0(model)) mf.gameObject.AddComponent<MeshCollider>().sharedMesh = mf.sharedMesh;
                if (item.dummy == "intact") intact = model;
                if (item.dummy == "worn") worn = model;
                if (item.hidden) model.SetActive(false);
            }
            var w = data.forest.world;
            Marker("SafePoint_A09", root, new Vector3(w.start.x, 0, w.start.z));
            Marker("RabbitBurrow_A02", root, new Vector3(w.burrow.x, 0, w.burrow.z));

            var rabbitSource = AssetDatabase.LoadAssetAtPath<GameObject>(RabbitModels + "/QingxiMountainRabbit_v003.fbx");
            if (rabbitSource == null) throw new InvalidOperationException("Rabbit v003 FBX was not imported");
            var rabbit = (GameObject)PrefabUtility.InstantiatePrefab(rabbitSource);
            rabbit.name = "ForestRabbit_v003 (Dondon look, Johnnnny0823 rig)";
            rabbit.transform.SetParent(root, false);
            var animation = rabbit.GetComponent<Animation>() ?? rabbit.AddComponent<Animation>();
            foreach (var clip in AssetDatabase.LoadAllAssetsAtPath(RabbitModels + "/QingxiMountainRabbit_v003.fbx").OfType<AnimationClip>().Where(c => !c.name.StartsWith("__preview")))
            {
                var name = new[] { "Rabbit_Idle", "Rabbit_Hop", "Rabbit_Flee", "Rabbit_Hit", "Rabbit_Death" }.FirstOrDefault(n => clip.name.EndsWith(n));
                if (name == null) continue;
                animation.AddClip(clip, name);
                animation[name].wrapMode = name == "Rabbit_Hit" || name == "Rabbit_Death" ? WrapMode.ClampForever : WrapMode.Loop;
            }
            if (animation.GetClipCount() < 4) throw new InvalidOperationException("Rabbit v003 legacy clips missing: " + animation.GetClipCount());
            animation.clip = animation.GetClip("Rabbit_Idle"); animation.playAutomatically = true;
            result.report.Add($"rabbit v003 clips: {animation.GetClipCount()}");

            var lane = new GameObject("RabbitChargeLane").AddComponent<LineRenderer>();
            lane.transform.SetParent(root, false);
            lane.positionCount = 2; lane.startWidth = .55f; lane.endWidth = .2f; lane.useWorldSpace = true;
            lane.sharedMaterial = Flat("ForestChargeLane", new Color(.86f, .36f, .22f, .55f));

            var encounter = root.gameObject.AddComponent<QingxiForestEncounter>();
            encounter.zoneData = AssetDatabase.LoadAssetAtPath<TextAsset>(DataPath);
            encounter.walker = player.GetComponent<global::QingxiWorld.QingxiFirstPerson>();
            encounter.rabbit = rabbit.transform; encounter.rabbitAnimation = animation; encounter.chargeLane = lane;
            encounter.dummyIntact = intact; encounter.dummyWorn = worn;
            result.encounter = encounter;
            return root;
        }

        // ------------------------------------------------------------------ B: alchemy corner
        static Transform BuildAlchemy(QingxiAbcZoneData data, Anchor anchor, Result result)
        {
            var root = Root("CollaboratorZone_B_AlchemyCorner (joshsu54)", anchor);
            foreach (var item in data.alchemy.layout)
            {
                var model = Kit(AlchemyModels + "/" + item.folder, item.id, item.id, root, new Vector3(item.x, item.y + LocalGround(root, item.x, item.z), item.z), item.yawDeg,
                    Path.Combine(Repo, "art/exports/qingxi-alchemy-b", item.folder, "v001", item.id + "_model_info.json"), result);
                if (item.y < .01f) Solid(model);
            }
            // Same graybox work table as AlchemyRoomBuilder: named as a placeholder, not an authored asset.
            var t = data.alchemy.table;
            var tableGround = LocalGround(root, t.x, t.z);
            var table = GameObject.CreatePrimitive(PrimitiveType.Cube);
            table.name = "Placeholder_WorkTable (graybox)";
            table.transform.SetParent(root, false);
            table.transform.localPosition = new Vector3(t.x, tableGround + t.y - .03f, t.z);
            table.transform.localScale = new Vector3(t.width, .06f, t.depth);
            table.GetComponent<Renderer>().sharedMaterial = Flat("AlchemyCornerTimber", new Color(.36f, .27f, .18f));
            foreach (var x in new[] { -1, 1 }) foreach (var z in new[] { -1, 1 })
            {
                var leg = GameObject.CreatePrimitive(PrimitiveType.Cube);
                leg.name = "Placeholder_TableLeg"; leg.transform.SetParent(root, false);
                leg.transform.localPosition = new Vector3(t.x + x * (t.width / 2 - .08f), tableGround + (t.y - .06f) / 2, t.z + z * (t.depth / 2 - .08f));
                leg.transform.localScale = new Vector3(.08f, t.y - .06f, .08f);
                leg.GetComponent<Renderer>().sharedMaterial = table.GetComponent<Renderer>().sharedMaterial;
            }
            result.alchemyDoor = Marker("AlchemyDoor_B", root, new Vector3(data.alchemy.door.x, 0, data.alchemy.door.z)).transform;
            return root;
        }

        // ------------------------------------------------------------------ C: return corner
        static Transform BuildReturn(QingxiAbcZoneData data, Anchor anchor, Result result)
        {
            var root = Root("CollaboratorZone_C_ReturnCorner (Eli-0731)", anchor);
            foreach (var item in data.ret.layout)
            {
                var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{ReturnModels}/{item.id}.fbx");
                if (source == null) throw new InvalidOperationException("Missing C model " + item.id);
                var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
                model.name = item.id + " - by Eli-0731";
                model.transform.SetParent(root, false);
                model.transform.localPosition = new Vector3(item.x, item.y + LocalGround(root, item.x, item.z), item.z);
                model.transform.localRotation = Quaternion.identity;
                foreach (var r in model.GetComponentsInChildren<Renderer>())
                    r.sharedMaterials = r.sharedMaterials.Select(m => ReturnMaterial(ReturnModels, item.id, m)).ToArray();
                if (item.y < .01f) Solid(model);
                result.models++;
            }
            result.returnTable = Marker("ReturnTable_C02", root, new Vector3(data.ret.table.x, 0, data.ret.table.z)).transform;
            return root;
        }

        // ------------------------------------------------------------------ shared helpers
        static GameObject Kit(string folder, string key, string name, Transform parent, Vector3 local, float yaw, string infoPath, Result result)
        {
            var source = AssetDatabase.LoadAssetAtPath<GameObject>($"{folder}/{key}.fbx");
            if (source == null) throw new InvalidOperationException($"Missing collaborator FBX {folder}/{key}.fbx");
            var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
            model.name = name;
            model.transform.SetParent(parent, false);
            model.transform.localPosition = local;
            model.transform.localRotation = Quaternion.Euler(0, yaw, 0);
            var material = KitMaterial(folder, key);
            foreach (var r in model.GetComponentsInChildren<Renderer>()) r.sharedMaterials = Enumerable.Repeat(material, r.sharedMaterials.Length).ToArray();
            var levels = new List<LOD>(); float[] cut = { .22f, .07f, .012f };
            for (int i = 0; i < 3; i++)
            {
                var rs = model.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD" + i)).ToArray();
                if (rs.Length > 0) levels.Add(new LOD(cut[i], rs));
            }
            if (levels.Count > 1 && model.GetComponent<LODGroup>() == null) { var group = model.AddComponent<LODGroup>(); group.SetLODs(levels.ToArray()); group.RecalculateBounds(); }
            if (File.Exists(infoPath))
            {
                var info = JsonUtility.FromJson<ModelInfo>(File.ReadAllText(infoPath));
                var b = Bounds(model);
                if (Mathf.Abs(b.size.y - info.dimensions_m[2]) > .03f)
                    throw new InvalidDataException($"{key} imported height {b.size.y:0.###} does not match model_info {info.dimensions_m[2]}");
                result.report.Add($"{key}: {b.size.x:0.##}×{b.size.z:0.##}×{b.size.y:0.##} m");
            }
            result.models++;
            return model;
        }

        static IEnumerable<MeshFilter> Lod0(GameObject model)
        {
            var all = model.GetComponentsInChildren<MeshFilter>();
            var lod0 = all.Where(m => m.name.EndsWith("_LOD0")).ToArray();
            return lod0.Length > 0 ? lod0 : all;
        }

        static Bounds Bounds(GameObject model)
        {
            var rs = model.GetComponentsInChildren<Renderer>().Where(r => r.name.EndsWith("_LOD0")).ToArray();
            if (rs.Length == 0) rs = model.GetComponentsInChildren<Renderer>();
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        static void Solid(GameObject model)
        {
            var b = Bounds(model);
            var box = model.AddComponent<BoxCollider>();
            box.center = model.transform.InverseTransformPoint(b.center);
            var size = model.transform.InverseTransformVector(b.size);
            box.size = new Vector3(Mathf.Abs(size.x), Mathf.Abs(size.y), Mathf.Abs(size.z));
        }

        static GameObject Marker(string name, Transform parent, Vector3 local)
        {
            var go = new GameObject(name); go.transform.SetParent(parent, false); go.transform.localPosition = local; return go;
        }

        // Follow whatever pipeline is active (the village builder sets URP) so the kits never render magenta.
        static bool Urp => GraphicsSettings.currentRenderPipeline != null;

        static Material KitMaterial(string folder, string key)
        {
            var path = $"{MaterialFolder}/{key}{(Urp ? "_URP" : "")}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find(Urp ? "Universal Render Pipeline/Lit" : "Standard")); AssetDatabase.CreateAsset(mat, path); }
            var baseColor = AssetDatabase.LoadAssetAtPath<Texture2D>($"{folder}/textures/T_{key}_BaseColor.png");
            var normal = AssetDatabase.LoadAssetAtPath<Texture2D>($"{folder}/textures/T_{key}_Normal.png");
            if (baseColor == null) throw new InvalidOperationException($"Missing base colour texture for {key}");
            bool bronze = key.StartsWith("B01") || key.StartsWith("B02");
            mat.SetTexture(Urp ? "_BaseMap" : "_MainTex", baseColor);
            mat.SetColor(Urp ? "_BaseColor" : "_Color", Color.white);
            if (normal != null) { mat.SetTexture("_BumpMap", normal); mat.EnableKeyword("_NORMALMAP"); }
            mat.SetFloat("_Metallic", bronze ? .55f : 0);
            mat.SetFloat(Urp ? "_Smoothness" : "_Glossiness", bronze ? .42f : key.StartsWith("B10") ? .6f : .12f);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // C's FBX keep Eli-0731's material names; textured ones get the PNG written beside the FBX by
        // tools/art/import_qingxi_return_c_to_unity.py, flat ones keep the imported colour and emission.
        static Material ReturnMaterial(string folder, string id, Material imported)
        {
            if (imported == null) return null;
            var name = imported.name.Split(' ')[0];
            var path = $"{MaterialFolder}/C_{id}_{name}{(Urp ? "_URP" : "")}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find(Urp ? "Universal Render Pipeline/Lit" : "Standard")); AssetDatabase.CreateAsset(mat, path); }
            var texturePath = AssetDatabase.FindAssets("t:Texture2D", new[] { folder + "/Textures" }).Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => Path.GetFileNameWithoutExtension(p).StartsWith($"{id}_{name}_"));
            var texture = texturePath == null ? null : AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
            var color = imported.HasProperty("_Color") ? imported.color : imported.HasProperty("_BaseColor") ? imported.GetColor("_BaseColor") : Color.white;
            mat.SetTexture(Urp ? "_BaseMap" : "_MainTex", texture);
            mat.SetColor(Urp ? "_BaseColor" : "_Color", texture != null ? Color.white : color);
            mat.SetFloat(Urp ? "_Smoothness" : "_Glossiness", .15f);
            if (imported.HasProperty("_EmissionColor") && imported.IsKeywordEnabled("_EMISSION"))
            {
                mat.SetColor("_EmissionColor", imported.GetColor("_EmissionColor")); mat.EnableKeyword("_EMISSION");
            }
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material Flat(string name, Color color)
        {
            var path = $"{MaterialFolder}/{name}{(Urp ? "_URP" : "")}.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find(Urp ? "Universal Render Pipeline/Unlit" : "Sprites/Default")); AssetDatabase.CreateAsset(mat, path); }
            mat.SetColor(Urp ? "_BaseColor" : "_Color", color);
            EditorUtility.SetDirty(mat);
            return mat;
        }

        // ------------------------------------------------------------------ copy and import collaborator exports
        static void CopyKits(QingxiAbcZoneData data)
        {
            var forestSource = Path.Combine(Repo, "art/exports/qingxi-encounter-a");
            Copy(forestSource, Path.Combine(Repo, "apps/game", ForestModels), "*.fbx");
            Copy(Path.Combine(forestSource, "textures"), Path.Combine(Repo, "apps/game", ForestModels, "textures"), "*.png");
            Copy(Path.Combine(Repo, "art/exports/qingxi-mountain-rabbit-v003"), Path.Combine(Repo, "apps/game", RabbitModels), "QingxiMountainRabbit_v003.fbx");
            var trainingSource = Path.Combine(Repo, "art/exports/qingxi-training-yard-v1");
            Copy(trainingSource, Path.Combine(Repo, "apps/game", TrainingModels), "*.fbx");
            Copy(Path.Combine(trainingSource, "textures"), Path.Combine(Repo, "apps/game", TrainingModels, "textures"), "*.png");
            foreach (var folder in data.alchemy.layout.Select(i => i.folder).Distinct())
            {
                var src = Path.Combine(Repo, "art/exports/qingxi-alchemy-b", folder, "v001");
                var dst = Path.Combine(Repo, "apps/game", AlchemyModels, folder);
                Copy(src, dst, "*.fbx");
                Copy(Path.Combine(src, "textures"), Path.Combine(dst, "textures"), "*.png");
            }
            AssetDatabase.Refresh();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { ForestModels, AlchemyModels, TrainingModels }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var importer = (ModelImporter)AssetImporter.GetAtPath(path);
                bool rabbit = path.StartsWith(RabbitModels);
                bool dirty = !importer.bakeAxisConversion || importer.importAnimation != rabbit ||
                    (rabbit ? importer.animationType != ModelImporterAnimationType.Legacy : importer.materialImportMode != ModelImporterMaterialImportMode.None);
                if (!dirty) continue;
                importer.bakeAxisConversion = true; importer.importCameras = false; importer.importLights = false; importer.addCollider = false;
                importer.importAnimation = rabbit;
                if (rabbit) importer.animationType = ModelImporterAnimationType.Legacy;
                else importer.materialImportMode = ModelImporterMaterialImportMode.None;
                importer.SaveAndReimport();
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { ForestModels, AlchemyModels, TrainingModels }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = AssetImporter.GetAtPath(path) as TextureImporter; if (ti == null) continue;
                bool normal = path.EndsWith("_Normal.png"), linear = normal || path.EndsWith("_ORM.png");
                var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
                if (ti.textureType == type && ti.sRGBTexture == !linear && ti.maxTextureSize == 1024) continue;
                ti.textureType = type; ti.sRGBTexture = !linear; ti.maxTextureSize = 1024; ti.mipmapEnabled = true; ti.SaveAndReimport();
            }
        }

        static void Copy(string sourceDir, string targetDir, string pattern)
        {
            if (!Directory.Exists(sourceDir)) throw new DirectoryNotFoundException(sourceDir);
            Directory.CreateDirectory(targetDir);
            foreach (var file in Directory.GetFiles(sourceDir, pattern))
            {
                if (new FileInfo(file).Length < 1024 && File.ReadAllText(file).StartsWith("version https://git-lfs"))
                    throw new InvalidOperationException("Git LFS pointer instead of asset; run git lfs pull: " + file);
                var target = Path.Combine(targetDir, Path.GetFileName(file));
                if (!File.Exists(target) || new FileInfo(target).Length != new FileInfo(file).Length) File.Copy(file, target, true);
            }
        }
    }
}
