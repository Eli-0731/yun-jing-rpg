using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace YunJing.Editor
{
    // K5: the blocks around the novice village (docs/execution/novice-world-block-plan.md), each its own scene
    // built from tools/qingxi-terrain/blocks/<id>.json: terrain (blending to the shared world height at its
    // edges, so it meets A1 without a seam), roads and pads, slot frames or models, the brook, trees and wind.
    // No lights or camera: QingxiBlockStreamer loads them additively into the village when the player comes near.
    public static class QingxiBlockBuilder
    {
        // Which side of each block faces A1 (left open; the other three sides are walled for now).
        public static readonly (string id, string open)[] Blocks = { ("A2", "north"), ("A3", "east") };

        public static string ScenePath(string id) => $"Assets/YunJing/Generated/QingxiBlock_{id}.unity";

        public static void GenerateAll()
        {
            foreach (var (id, open) in Blocks) Generate(id, open);
        }

        static void Generate(string id, string open)
        {
            var layout = QingxiVillageTerrain.Load($"tools/qingxi-terrain/blocks/{id}.json");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("QingxiBlock_" + id).transform;
            var terrain = QingxiVillageTerrain.Create(root, layout, "BlockTerrain_" + id, $"BlockTerrain_{id} (blocks/{id}.json)");
            Physics.SyncTransforms();
            QingxiNoviceVillageBuilder.BuildBlock(root, layout, terrain);
            Walls(root, layout.bounds, open);
            Directory.CreateDirectory(Path.GetDirectoryName(ScenePath(id)));
            if (!EditorSceneManager.SaveScene(scene, ScenePath(id))) throw new IOException("Could not save " + ScenePath(id));
            Debug.Log($"QINGXI_BLOCK_GENERATED {id}: {layout.pads.Length} pads, {layout.edges.Length} roads, {layout.placements.Length} slots -> {ScenePath(id)}");
        }

        // Invisible walls 2 m inside the closed edges (the open edge joins A1).
        static void Walls(Transform root, QingxiVillageTerrain.Area a, string open)
        {
            float x0 = a.minX + 2, x1 = a.minX + a.sizeX - 2, z0 = a.minZ + 2, z1 = a.minZ + a.sizeZ - 2, cx = (x0 + x1) / 2, cz = (z0 + z1) / 2;
            foreach (var (side, x, z, w, d) in new[] { ("north", cx, z1, a.sizeX, 1f), ("south", cx, z0, a.sizeX, 1f), ("east", x1, cz, 1f, a.sizeZ), ("west", x0, cz, 1f, a.sizeZ) })
            {
                if (side == open) continue;
                var wall = new GameObject("Boundary " + side); wall.transform.SetParent(root, false);
                wall.transform.position = new Vector3(x, 5, z);
                wall.AddComponent<BoxCollider>().size = new Vector3(w, 12, d);
            }
        }
    }
}
