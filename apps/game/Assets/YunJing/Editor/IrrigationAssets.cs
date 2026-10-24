using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.Editor
{
    public static class IrrigationAssets
    {
        const string Source = "Assets/YunJing/Models/IrrigationV2";
        const string Destination = "Assets/YunJing/Generated/Irrigation";

        static Texture2D Texture(string asset, string channel)
        {
            string path = Source + "/Textures/" + asset + "-" + channel + ".png";
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new FileNotFoundException("Missing baked model texture", path);
            importer.textureType = channel == "normal" ? TextureImporterType.NormalMap : TextureImporterType.Default;
            importer.sRGBTexture = channel != "normal";
            importer.convertToNormalmap = false;
            importer.mipmapEnabled = true; importer.isReadable = false;
            importer.maxTextureSize = 1024; importer.wrapMode = TextureWrapMode.Clamp;
            importer.textureCompression = TextureImporterCompression.Compressed;
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        static Material Surface(string asset, bool water, Texture2D albedo, Texture2D normal)
        {
            string path = Destination + "/" + asset + (water ? "-water" : "-surface") + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                var shader = Shader.Find("Universal Render Pipeline/Lit");
                if (shader == null) throw new InvalidOperationException("URP Lit shader is unavailable.");
                material = new Material(shader); AssetDatabase.CreateAsset(material, path);
            }
            material.SetColor("_BaseColor", Color.white); material.SetTexture("_BaseMap", albedo);
            material.SetTexture("_BumpMap", normal); material.SetFloat("_BumpScale", 1);
            material.EnableKeyword("_NORMALMAP");
            material.SetFloat("_Smoothness", water ? .73f : .22f);
            material.SetFloat("_Metallic", water ? .08f : 0);
            material.SetFloat("_Cull", (float)CullMode.Off); // Thin low-poly leaves have two visible sides.
            EditorUtility.SetDirty(material); return material;
        }

        public static GameObject Place(string asset, string name, Vector3 position, Vector3 collisionSize)
        {
            Directory.CreateDirectory(Destination); AssetDatabase.Refresh();
            var albedo = Texture(asset, "albedo"); var normal = Texture(asset, "normal");
            var surface = Surface(asset, false, albedo, normal); var water = Surface(asset, true, albedo, normal);
            var root = new GameObject(name); var foliageParts = new List<GameObject>(); var waterParts = new List<GameObject>();
            var levels = new LOD[2];
            for (int level = 0; level < 2; level++)
            {
                string path = Source + "/" + asset + (level == 0 ? "" : "-lod1") + ".fbx";
                var source = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (source == null) throw new FileNotFoundException("Missing model LOD", path);
                var model = (GameObject)PrefabUtility.InstantiatePrefab(source);
                model.name = "LOD" + level; model.transform.SetParent(root.transform, false);
                var renderers = model.GetComponentsInChildren<Renderer>();
                foreach (var renderer in renderers)
                {
                    string meshName = renderer.gameObject.name;
                    bool isWater = meshName.EndsWith("-water") || meshName.EndsWith("-water-lod1");
                    renderer.sharedMaterials = new[] { isWater ? water : surface };
                    if (meshName.Contains("-foliage")) foliageParts.Add(renderer.gameObject);
                    if (isWater) waterParts.Add(renderer.gameObject);
                }
                levels[level] = new LOD(level == 0 ? .14f : .015f, renderers);
            }
            var group = root.AddComponent<LODGroup>(); group.SetLODs(levels); group.RecalculateBounds();
            var visual = root.AddComponent<IrrigationVisual>();
            visual.Foliage = foliageParts.ToArray(); visual.Water = waterParts.ToArray();
            var collider = root.AddComponent<BoxCollider>(); collider.size = collisionSize;
            collider.center = Vector3.up * collisionSize.y * .5f;
            PrefabUtility.SaveAsPrefabAsset(root, Destination + "/" + asset + ".prefab");
            root.transform.position = position;
            return root;
        }
    }
}
