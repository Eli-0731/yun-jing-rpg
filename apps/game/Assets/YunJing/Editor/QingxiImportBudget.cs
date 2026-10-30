using UnityEditor;
using UnityEngine;

namespace YunJing.Editor
{
    // Download budget for the browser build (target ≤ 50 MB). Applied when models and their textures import,
    // so collaborators' files and .meta settings stay as delivered:
    //   - meshes: medium mesh compression (positions/normals/UVs quantised; invisible at game distances);
    //   - textures: at most 1024 px, crunch-compressed (much smaller download, decoded on load).
    // Bump Version to reimport everything after changing a rule.
    public sealed class QingxiImportBudget : AssetPostprocessor
    {
        const uint Version = 1;
        static readonly string[] Folders = { "Assets/YunJing/Models/", "Assets/QingxiWorld/Models/" };

        public override uint GetVersion() => Version;

        static bool InBudget(string path)
        {
            foreach (var f in Folders) if (path.StartsWith(f)) return true;
            return false;
        }

        void OnPreprocessModel()
        {
            if (!InBudget(assetPath)) return;
            var model = (ModelImporter)assetImporter;
            model.meshCompression = ModelImporterMeshCompression.Medium;
        }

        void OnPreprocessTexture()
        {
            if (!InBudget(assetPath)) return;
            var texture = (TextureImporter)assetImporter;
            texture.maxTextureSize = Mathf.Min(texture.maxTextureSize, 1024);
            texture.textureCompression = TextureImporterCompression.Compressed;
            texture.crunchedCompression = true;
            texture.compressionQuality = 50;
        }

        // Batch entry point: reimport the model folders once so the rules apply to existing assets.
        public static void ReimportAll()
        {
            foreach (var f in Folders)
                AssetDatabase.ImportAsset(f.TrimEnd('/'), ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);
            Debug.Log("QINGXI_IMPORT_BUDGET reimported " + string.Join(", ", Folders));
        }
    }
}
