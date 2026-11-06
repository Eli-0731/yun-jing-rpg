using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace YunJing.CreekRepair
{
    // A bed of mud as heights on a grid, so the spade really moves it. The blade cuts down from what was there when the stroke
    // began, whatever it cuts rides up in front of it as a bow, and the bow spills out to the sides. Nothing appears or vanishes
    // except what Heave and Remove take away, so a thin place and a stone showing through it are simply what is left.
    // Vertices are in world space. The grid lines up with the world axes, as the channels do.
    public sealed class CreekMudBed
    {
        public const float Hidden = .002f;
        public readonly GameObject go; public readonly Mesh mesh; public readonly float cell, floorY;
        public float StartVolume { get; private set; }
        public float Removed { get; private set; }
        public float Carried => carry * cell * cell;
        readonly int nx, nz; readonly float ox, oz; readonly float[] h, h0, hold, grain, lump; bool[] wall; readonly Vector3[] v, n; readonly Vector2[] cut;
        float carry, settleFor; Vector2 settleAt; bool dirty, seeping;

        public CreekMudBed(string name, Transform parent, Material material, Vector3 centre, float sizeX, float sizeZ, float cell, float uvPerMetre)
        {
            this.cell = cell; floorY = centre.y;
            nx = Mathf.CeilToInt(sizeX / cell) + 1; nz = Mathf.CeilToInt(sizeZ / cell) + 1; ox = centre.x - (nx - 1) * cell / 2; oz = centre.z - (nz - 1) * cell / 2;
            int count = nx * nz; h = new float[count]; h0 = new float[count]; grain = new float[count]; hold = new float[count]; lump = new float[count]; v = new Vector3[count]; n = new Vector3[count]; cut = new Vector2[count];
            var uv = new Vector2[count]; var tangents = new Vector4[count]; var colors = new Color32[count]; var tris = new int[(nx - 1) * (nz - 1) * 6];
            for (int z = 0, i = 0; z < nz; z++) for (int x = 0; x < nx; x++, i++)
            {
                float wx = ox + x * cell, wz = oz + z * cell;
                uv[i] = new Vector2(wx, wz) * uvPerMetre; tangents[i] = new Vector4(1, 0, 0, -1); colors[i] = new Color32(255, 255, 255, 255); n[i] = Vector3.up;
                lump[i] = (Mathf.PerlinNoise(wx * 9 + 31, wz * 9 + 17) - .5f) * .05f + (Mathf.PerlinNoise(wx * 21 + 7, wz * 21 + 23) - .5f) * .018f;
                hold[i] = .45f + 1.3f * Mathf.PerlinNoise(wx * 4.3f + 11, wz * 4.3f + 5) + .35f * Mathf.PerlinNoise(wx * 13 + 2, wz * 13 + 9);
                grain[i] = (Mathf.PerlinNoise(wx * 16 + 3, wz * 16 + 7) - .5f) * .006f;   // the blade's edge is not straight: it leaves a combed surface
            }
            for (int z = 0, t = 0; z < nz - 1; z++) for (int x = 0; x < nx - 1; x++)
            {
                int a = z * nx + x; tris[t++] = a; tris[t++] = a + nx; tris[t++] = a + 1; tris[t++] = a + 1; tris[t++] = a + nx; tris[t++] = a + nx + 1;
            }
            mesh = new Mesh { name = name, indexFormat = count > 65000 ? IndexFormat.UInt32 : IndexFormat.UInt16 }; mesh.MarkDynamic(); Fill();
            mesh.SetVertices(v); mesh.SetNormals(n); mesh.SetUVs(0, uv); mesh.SetUVs(3, cut); mesh.SetTangents(tangents); mesh.SetColors(colors); mesh.SetTriangles(tris, 0);
            mesh.bounds = new Bounds(centre + Vector3.up * .4f, new Vector3(sizeX + .2f, 1, sizeZ + .2f));
            go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer)); go.transform.SetParent(parent, false); go.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity);
            go.GetComponent<MeshFilter>().sharedMesh = mesh; var look = go.GetComponent<MeshRenderer>(); look.sharedMaterial = material; look.shadowCastingMode = ShadowCastingMode.On;
            var carved = new MaterialPropertyBlock(); carved.SetFloat("_Carved", 1); look.SetPropertyBlock(carved);
        }

        // ---- shape --------------------------------------------------------------------------------------------------
        public void Profile(Func<float, float, float> height)
        {
            for (int z = 0, i = 0; z < nz; z++) for (int x = 0; x < nx; x++, i++) h[i] = Mathf.Max(0, height(ox + x * cell, oz + z * cell));
            Settled();
        }

        /// Takes the top of a modelled heap as this bed's first shape.
        public void Stamp(Mesh heap, Matrix4x4 toWorld)
        {
            var verts = heap.vertices; var tris = heap.triangles;
            for (int i = 0; i < verts.Length; i++) verts[i] = toWorld.MultiplyPoint3x4(verts[i]);
            for (int t = 0; t < tris.Length; t += 3)
            {
                Vector3 a = verts[tris[t]], b = verts[tris[t + 1]], c = verts[tris[t + 2]];
                int x0 = Mathf.Max(0, Mathf.FloorToInt((Mathf.Min(a.x, b.x, c.x) - ox) / cell)), x1 = Mathf.Min(nx - 1, Mathf.CeilToInt((Mathf.Max(a.x, b.x, c.x) - ox) / cell));
                int z0 = Mathf.Max(0, Mathf.FloorToInt((Mathf.Min(a.z, b.z, c.z) - oz) / cell)), z1 = Mathf.Min(nz - 1, Mathf.CeilToInt((Mathf.Max(a.z, b.z, c.z) - oz) / cell));
                float d = (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z); if (Mathf.Abs(d) < 1e-8f) continue;
                for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
                {
                    float wx = ox + x * cell, wz = oz + z * cell, u = ((b.z - c.z) * (wx - c.x) + (c.x - b.x) * (wz - c.z)) / d, w = ((c.z - a.z) * (wx - c.x) + (a.x - c.x) * (wz - c.z)) / d, s = 1 - u - w;
                    if (u < -.001f || w < -.001f || s < -.001f) continue;
                    float y = u * a.y + w * b.y + s * c.y - floorY; int i = z * nx + x; if (y > h[i]) h[i] = y;
                }
            }
            for (int round = 0; round < 3; round++) Blur();
            Settled();
        }

        void Blur()
        {
            var was = (float[])h.Clone();
            for (int z = 1; z < nz - 1; z++) for (int x = 1; x < nx - 1; x++) { int i = z * nx + x; h[i] = (was[i] * 4 + was[i - 1] + was[i + 1] + was[i - nx] + was[i + nx]) / 8; }
        }

        /// Lets the first shape come to rest, so the first stroke moves mud the blade touched and not a slope that was waiting to give way.
        public void Rest()
        {
            for (int r = 0; r < 240; r++) for (int z = 0; z < nz; z++) for (int x = 0; x < nx; x++)
            {
                int i = z * nx + x;
                if (x < nx - 1) Ease(i, i + 1, cell * .85f * Slump);
                if (z < nz - 1) { Ease(i, i + nx, cell * .85f * Slump); if (x < nx - 1) Ease(i, i + nx + 1, cell * .85f * Slump * 1.41f); if (x > 0) Ease(i, i + nx - 1, cell * .85f * Slump * 1.41f); }
            }
            Settled();
        }

        void Settled() { StartVolume = Volume(); Removed = 0; carry = 0; dirty = true; }

        // ---- reading ------------------------------------------------------------------------------------------------
        public float Volume() { float sum = 0; foreach (var c in h) sum += c; return sum * cell * cell; }
        public float Progress => StartVolume <= 0 ? 1 : Mathf.Clamp01(Removed / StartVolume);

        public float DepthAt(Vector3 at)
        {
            float fx = (at.x - ox) / cell, fz = (at.z - oz) / cell; int x = Mathf.FloorToInt(fx), z = Mathf.FloorToInt(fz);
            if (x < 0 || z < 0 || x >= nx - 1 || z >= nz - 1) return 0;
            fx -= x; fz -= z; int i = z * nx + x;
            return Mathf.Lerp(Mathf.Lerp(h[i], h[i + 1], fx), Mathf.Lerp(h[i + nx], h[i + nx + 1], fx), fz);
        }
        public float SurfaceAt(Vector3 at) => floorY + DepthAt(at);

        /// The deepest place inside `zone`, smoothed over about a blade's width: where a player would go next.
        public Vector3 Deepest(Rect zone)
        {
            float best = -1; var at = new Vector3(zone.center.x, floorY, zone.center.y); const float Step = .04f;
            for (float z = zone.yMin; z <= zone.yMax; z += Step) for (float x = zone.xMin; x <= zone.xMax; x += Step)
            {
                float d = 0; for (int k = 0; k < 5; k++) d += DepthAt(new Vector3(x + (k == 1 ? .08f : k == 2 ? -.08f : 0), 0, z + (k == 3 ? .08f : k == 4 ? -.08f : 0)));
                if (d > best) { best = d; at = new Vector3(x, floorY + d / 5, z); }
            }
            return at;
        }

        // ---- the blade ----------------------------------------------------------------------------------------------
        public void BeginStroke() => Array.Copy(h, h0, h.Length);

        /// The blade moves `from` to `to` at the depth this mud lets it bite. What it cuts is laid down just ahead of it.
        public void Sweep(Vector2 from, Vector2 to, float halfWidth, float bite)
        {
            var delta = to - from; float length = delta.magnitude; if (length < 1e-5f) return;
            var d = delta / length; var p = new Vector2(-d.y, d.x); int steps = Mathf.CeilToInt(length / (cell * .6f));
            const float Back = .03f, Lead = .008f, BowLength = .075f; float reach = halfWidth + BowLength + Back;
            for (int s = 1; s <= steps; s++)
            {
                var c = from + delta * s / steps; float take = carry; carry = 0; float weights = 0;
                int x0 = Mathf.Max(0, Mathf.FloorToInt((c.x - reach - ox) / cell)), x1 = Mathf.Min(nx - 1, Mathf.CeilToInt((c.x + reach - ox) / cell));
                int z0 = Mathf.Max(0, Mathf.FloorToInt((c.y - reach - oz) / cell)), z1 = Mathf.Min(nz - 1, Mathf.CeilToInt((c.y + reach - oz) / cell));
                for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
                {
                    var rel = new Vector2(ox + x * cell - c.x, oz + z * cell - c.y); float along = Vector2.Dot(rel, d), side = Mathf.Abs(Vector2.Dot(rel, p));
                    if (side >= halfWidth) continue; int i = z * nx + x;
                    if (along > -Back && along <= Lead)
                    {
                        float edge = Mathf.SmoothStep(0, 1, (side - halfWidth * .55f) / (halfWidth * .45f));   // the blade is curved: it cuts deepest in the middle, nothing at its corners
                        float limit = Mathf.Max(0, Mathf.Min(h0[i], h0[i] - bite * (1 - edge) + grain[i] * (1 - edge)));
                        if (h[i] > limit) { take += h[i] - limit; h[i] = limit; cut[i].x = 1; }
                    }
                    else if (along > Lead && along < Lead + BowLength) weights += (1 - (along - Lead) / BowLength) * (1 - .55f * side / halfWidth);
                }
                if (weights <= 0) { carry = take; continue; }   // nothing ahead but a wall: it stays pressed against the blade
                for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
                {
                    var rel = new Vector2(ox + x * cell - c.x, oz + z * cell - c.y); float along = Vector2.Dot(rel, d), side = Mathf.Abs(Vector2.Dot(rel, p));
                    if (side < halfWidth && along > Lead && along < Lead + BowLength) h[z * nx + x] += take * (1 - (along - Lead) / BowLength) * (1 - .55f * side / halfWidth) / weights;
                }
            }
            seeping = true; dirty = true;
        }

        /// Wet mud stands only so steep: what is over that runs down to its neighbours, which makes the sides of the bow.
        public void Slide(Vector2 at, float radius, int rounds)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt((at.x - radius - ox) / cell)), x1 = Mathf.Min(nx - 1, Mathf.CeilToInt((at.x + radius - ox) / cell));
            int z0 = Mathf.Max(0, Mathf.FloorToInt((at.y - radius - oz) / cell)), z1 = Mathf.Min(nz - 1, Mathf.CeilToInt((at.y + radius - oz) / cell));
            float steep = cell * .85f * Slump;
            for (int r = 0; r < rounds; r++) for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
            {
                int i = z * nx + x;
                if (x < nx - 1) Ease(i, i + 1, steep);
                if (z < nz - 1) { Ease(i, i + nx, steep); if (x < nx - 1) Ease(i, i + nx + 1, steep * 1.41f); if (x > 0) Ease(i, i + nx - 1, steep * 1.41f); }
            }
            dirty = true;
        }

        /// Thrown mud lies lower than a plug that walls hold up.
        public float Slump = 1;

        /// Mud does not run through what stands here.
        public void Block(Rect area)
        {
            wall = new bool[h.Length];
            for (int z = 0, i = 0; z < nz; z++) for (int x = 0; x < nx; x++, i++) wall[i] = area.Contains(new Vector2(ox + x * cell, oz + z * cell));
        }

        /// After a stroke the mud goes on sagging for a moment.
        public void Settle(Vector2 at) { settleAt = at; settleFor = 1.6f; }

        /// Wet mud has no crisp edge: a cell that stands off from its neighbours gives way to them, which loses the saw teeth a grid leaves along a ridge. A broad slope is left alone, so a heap cannot creep out into a sheet. Only moves mud, never makes or loses any.
        void Relax(Vector2 at, float radius, int rounds)
        {
            int x0 = Mathf.Max(1, Mathf.FloorToInt((at.x - radius - ox) / cell)), x1 = Mathf.Min(nx - 2, Mathf.CeilToInt((at.x + radius - ox) / cell));
            int z0 = Mathf.Max(1, Mathf.FloorToInt((at.y - radius - oz) / cell)), z1 = Mathf.Min(nz - 2, Mathf.CeilToInt((at.y + radius - oz) / cell));
            const float Tooth = .003f;
            for (int r = 0; r < rounds; r++) for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
            {
                int i = z * nx + x; float off = h[i] - (h[i - 1] + h[i + 1] + h[i - nx] + h[i + nx]) / 4;
                if (Mathf.Abs(off) < Tooth) continue;
                float give = off * .5f; if (give < 0) { float least = Mathf.Min(h[i - 1], Mathf.Min(h[i + 1], Mathf.Min(h[i - nx], h[i + nx]))); give = -Mathf.Min(-give, least * 4); }
                h[i] -= give; h[i - 1] += give / 4; h[i + 1] += give / 4; h[i - nx] += give / 4; h[i + nx] += give / 4;
            }
            dirty = true;
        }

        void Ease(int a, int b, float steep)
        {
            if (wall != null && (wall[a] || wall[b])) return;
            float d = h[a] - h[b], over = Mathf.Abs(d) - steep * hold[d > 0 ? a : b]; if (over <= 0) return;
            float move = over * .24f * Mathf.Sign(d); h[a] -= move; h[b] += move;
        }

        /// How much mud is riding in front of the blade: what stands above where the surface was when the stroke began.
        public float Bow(Vector2 at, float radius = .34f)
        {
            float sum = carry; ForEachNear(at, radius, i => { if (h[i] > h0[i]) sum += h[i] - h0[i]; });
            return sum * cell * cell;
        }

        /// Lifts the bow off and away. Returns the volume that left.
        public float Heave(Vector2 at, float radius = .34f)
        {
            float sum = carry; carry = 0;
            ForEachNear(at, radius, i => { if (h[i] > h0[i]) { sum += h[i] - h0[i]; h[i] = h0[i]; } });
            float gone = sum * cell * cell; Removed += gone; dirty = true; return gone;
        }

        /// A slope letting go by itself: this much leaves from round `at`, most from the middle.
        public float Remove(Vector2 at, float radius, float volume)
        {
            float have = 0; ForEachNear(at, radius, i => have += h[i] * Falloff(i, at, radius)); have *= cell * cell;
            float k = have <= 0 ? 0 : Mathf.Min(1, volume / have), gone = 0;
            ForEachNear(at, radius, i => { float take = h[i] * Falloff(i, at, radius) * k; h[i] -= take; gone += take; cut[i].x = Mathf.Max(cut[i].x, k); });
            gone *= cell * cell; Removed += gone; seeping = true; dirty = true; return gone;
        }

        /// What a slump owes beyond what its own patch held comes off everywhere.
        public void Thin(float volume)
        {
            float have = Volume(); if (have <= 0 || volume <= 0) return;
            float k = Mathf.Clamp01(1 - volume / have); for (int i = 0; i < h.Length; i++) h[i] *= k;
            Removed += have * (1 - k); dirty = true;
        }

        float Falloff(int i, Vector2 at, float radius)
        {
            float d = new Vector2(ox + i % nx * cell - at.x, oz + i / nx * cell - at.y).magnitude / radius; return d >= 1 ? 0 : 1 - d * d;
        }

        void ForEachNear(Vector2 at, float radius, Action<int> visit)
        {
            int x0 = Mathf.Max(0, Mathf.FloorToInt((at.x - radius - ox) / cell)), x1 = Mathf.Min(nx - 1, Mathf.CeilToInt((at.x + radius - ox) / cell));
            int z0 = Mathf.Max(0, Mathf.FloorToInt((at.y - radius - oz) / cell)), z1 = Mathf.Min(nz - 1, Mathf.CeilToInt((at.y + radius - oz) / cell));
            float r2 = radius * radius;
            for (int z = z0; z <= z1; z++) for (int x = x0; x <= x1; x++)
            {
                float dx = ox + x * cell - at.x, dz = oz + z * cell - at.y;
                if (dx * dx + dz * dz <= r2) visit(z * nx + x);
            }
        }

        /// A saved game comes back with this share already gone, taken off evenly.
        public void AlreadyGone(float share)
        {
            for (int i = 0; i < h.Length; i++) { h[i] *= 1 - share; if (share > 0) cut[i].x = 1; }
            Removed = StartVolume * share; dirty = true;
        }

        /// The last thin skin of a finished pile drains away by itself.
        public void Drain(float seconds)
        {
            float k = Mathf.Exp(-seconds * 2.2f); bool any = false;
            for (int i = 0; i < h.Length; i++) { if (h[i] <= 0) continue; h[i] *= k; if (h[i] < .001f) h[i] = 0; else any = true; }
            if (any || go.activeSelf) dirty = true;
            if (!any) go.SetActive(false);
        }

        /// Mud that came down here: it adds to the heap, which spreads as it grows.
        public void Land(Vector3 at, float volume, float radius = .1f)
        {
            float weights = 0; var flat = new Vector2(at.x, at.z);
            ForEachNear(flat, radius, i => weights += Falloff(i, flat, radius)); if (weights <= 0) return;
            float each = volume / (cell * cell) / weights; ForEachNear(flat, radius, i => h[i] += each * Falloff(i, flat, radius));
            Slide(flat, radius * 2.6f, 5); dirty = true;
        }

        // ---- showing it ---------------------------------------------------------------------------------------------
        /// A skin sits just under the floor, so its edge is a smooth line; where a bed that stains has had mud, a wet film stays on the floor, so scraped ground doesn't end at a paper-cut edge.
        float Surface(int i)
        {
            float y = h[i] - .012f + lump[i] * Mathf.Min(1, h[i] / .06f);
            if (!Stains) return y;
            if (h[i] > .012f) stained[i] = true;
            return stained[i] ? Mathf.Max(y, .0015f) : y;
        }
        /// Whether scraped ground keeps a film of what lay on it.
        public bool Stains { get => stained != null; set => stained = value ? new bool[h.Length] : null; }
        bool[] stained;

        void Fill()
        {
            for (int z = 0, i = 0; z < nz; z++) for (int x = 0; x < nx; x++, i++) v[i] = new Vector3(ox + x * cell, floorY + Surface(i), oz + z * cell);
            float two = cell * 2;
            for (int z = 0; z < nz; z++) for (int x = 0; x < nx; x++)
            {
                int i = z * nx + x; float l = v[x > 0 ? i - 1 : i].y, r = v[x < nx - 1 ? i + 1 : i].y, b = v[z > 0 ? i - nx : i].y, t = v[z < nz - 1 ? i + nx : i].y;
                n[i] = new Vector3(l - r, two * .6f, b - t).normalized;   // a little steeper than true, so a shallow furrow reads from up here
            }
        }

        /// Cut faces get wetter for six seconds; the grid goes to the GPU once a frame at most.
        public void Tick(float seconds)
        {
            if (seeping)
            {
                bool more = false; float step = seconds / 6;
                for (int i = 0; i < cut.Length; i++) if (cut[i].y < cut[i].x) { cut[i].y = Mathf.Min(cut[i].x, cut[i].y + step); more = true; }
                seeping = more; mesh.SetUVs(3, cut);
            }
            if (settleFor > 0) { settleFor -= seconds; Relax(settleAt, .85f, 2); }
            if (!dirty) return;
            dirty = false; Fill(); mesh.SetVertices(v); mesh.SetNormals(n);
        }
    }
}
