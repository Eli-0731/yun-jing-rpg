// Shared layout for the A/B/C zones of the Qingxi main scene. Read by build-data.mjs
// (Unity data) and by tools/qingxi-trial (browser). Coordinates are zone-local metres on
// the ground plane (x, z); the forest numbers are copied unchanged from
// tools/qingxi-encounter-a/app.mjs (Johnnnny0823) so the encounter plays as authored.

// ------------------------------------------------------------------ A: forest rabbit encounter
export const forestLayout = [
  { id: 'A02_HollowTile', x: 0, y: -0.6, z: 0, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: -2, y: -0.6, z: 5, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: 2, y: -0.6, z: 5, rot: Math.PI, terrain: true },
  { id: 'A01_SlopeTile', x: 5, y: -0.6, z: 1, rot: Math.PI / 2, terrain: true },
  { id: 'A07_RabbitTrailTile', x: 0, y: -0.15, z: -5.0, rot: 0, terrain: true },
  { id: 'A04_MossBoulderCover', x: -2.6, y: 0, z: -3.2, rot: 0.3 },
  { id: 'A05_LayeredRockCover', x: 3.4, y: 0, z: -1.2, rot: -1.2 },
  { id: 'A03_FallenLog', x: 3.6, y: 0, z: -5.2, rot: -0.45 },
  { id: 'A06_RootStump', x: -3.0, y: 0, z: -6.4, rot: 0.6 },
  { id: 'A08_BrokenBambooFence', x: -2.4, y: 0, z: -8.6, rot: 0 },
  { id: 'A08_BrokenBambooFence', x: 2.4, y: 0, z: -8.6, rot: Math.PI },
  { id: 'A11_WarningClothRack', x: 1.75, y: 0, z: -8.15, rot: Math.PI },
  { id: 'A10_WatchPlatform', x: -6.2, y: 0, z: -7.5, rot: Math.PI / 2 },
  { id: 'A09_StoneShelter', x: 0, y: 0, z: -11, rot: 0, floor: true },
  { id: 'A12_VineDummy', x: 3.4, y: 0, z: -10.6, rot: -Math.PI / 2, dummy: 'intact' },
  { id: 'A12_VineDummy_worn', x: 3.4, y: 0, z: -10.6, rot: -Math.PI / 2, dummy: 'worn', hidden: true },
];
const SAFE = { x: 0, z: -11 }, START = { x: 0, z: -9.95 };
const BURROW = { x: 0, z: 1.75 };
export const platform = { x: -6.2, z: -7.5, deck: 1.8, ladder: { x: -4.45, z: -7.5 } };
const DUMMY = { x: 3.4, z: -10.6, r: 0.3, wearAt: 8 };
const ring = (cx, cz, x0, x1, z0, z1, r = 0.22) => {
  const out = [], n = Math.max(1, Math.round(Math.hypot(x1 - x0, z1 - z0) / 0.4));
  for (let i = 0; i <= n; i++) out.push({ x: cx + x0 + (x1 - x0) * i / n, z: cz + z0 + (z1 - z0) * i / n, r });
  return out;
};
export const forestWorld = {
  burrow: BURROW, safe: SAFE, start: START, respawn: START, safeZones: [], dummies: [DUMMY],
  cover: [{ x: -2.6, z: -3.2, r: 0.95 }, { x: 3.4, z: -1.2, r: 1.25 }, { x: 3.6, z: -5.2, r: 0.5 }, { x: 2.5, z: -4.6, r: 0.5 }, { x: 4.7, z: -5.8, r: 0.5 }],
  walls: [{ x: -2.6, z: -3.2, r: 0.85 }, { x: 3.4, z: -1.2, r: 1.0 }, { x: 3.6, z: -5.2, r: 0.38 }, { x: 2.5, z: -4.6, r: 0.38 },
    { x: 4.7, z: -5.8, r: 0.38 }, { x: -3.0, z: -6.4, r: 0.5 },
    ...ring(-2.4, -8.6, -1.5, 1.5, 0, 0, 0.18), ...ring(2.4, -8.6, -1.5, 1.5, 0, 0, 0.18),
    ...ring(0, -11, -1.0, 1.0, -0.63, -0.63), ...ring(0, -11, -0.93, -0.93, 0.5, -0.5), ...ring(0, -11, 0.93, 0.93, 0.5, -0.5),
    { x: -0.98, z: -10.32, r: 0.12 }, { x: 0.98, z: -10.32, r: 0.12 },
    ...[-1, 1].flatMap(a => [-1, 1].map(b => ({ x: platform.x + 0.9 * a, z: platform.z + 0.9 * b, r: 0.13 }))),
    { x: DUMMY.x, z: DUMMY.z, r: 0.3 }, { x: 1.75, z: -8.15, r: 0.12 }],
};

// ------------------------------------------------------------------ B: open-air alchemy corner by the market
// Positions and Unity yaw (degrees) copied from joshsu54's AlchemyRoomBuilder; tabletop items keep his
// 0.78 m height on a work table. The playable workshop itself stays in his AlchemyRoom scene.
export const alchemyLayout = [
  { id: 'B01_BronzeFurnace_cold', folder: 'B01_BronzeFurnace', x: 0, y: 0, z: 1.6, yawDeg: 0 },
  { id: 'B02_FurnaceLid', folder: 'B02_FurnaceLid', x: 0, y: 0.746, z: 1.6, yawDeg: 0 },
  { id: 'B12_WorkshopChimney', folder: 'B12_WorkshopChimney', x: -1.3, y: 0, z: 2.15, yawDeg: 0 },
  { id: 'B07_WoodenFuelBox', folder: 'B07_WoodenFuelBox', x: -1.45, y: 0, z: 0.55, yawDeg: 0 },
  { id: 'B06_CeramicWaterJar', folder: 'B06_CeramicWaterJar', x: -2.55, y: 0, z: -0.55, yawDeg: 70 },
  { id: 'B05_HerbDrawerCabinet', folder: 'B05_HerbDrawerCabinet', x: 2.75, y: 0, z: 1.55, yawDeg: 90 },
  { id: 'B03_StoneMortar', folder: 'B03_StoneMortar', x: 0.95, y: 0.78, z: -0.9, yawDeg: 180 },
  { id: 'B08_VentilatedDryingBasket', folder: 'B08_VentilatedDryingBasket', x: 1.6, y: 0.78, z: -0.82, yawDeg: 180 },
  { id: 'B10_WaxSealedBottle_filled', folder: 'B10_WaxSealedBottle', x: 2.15, y: 0.78, z: -1.0, yawDeg: 180 },
  { id: 'B04_BambooSortingTrays', folder: 'B04_BambooSortingTrays', x: 0.95, y: 0, z: -1.65, yawDeg: 180 },
  { id: 'B11_BambooRecipeStand', folder: 'B11_BambooRecipeStand', x: 2.35, y: 0.78, z: -0.72, yawDeg: 180 },
  { id: 'B09_ClothFilterFrame', folder: 'B09_ClothFilterFrame', x: -2.6, y: 0, z: 1.75, yawDeg: 60 },
];
export const alchemyTable = { x: 1.55, y: 0.75, z: -0.85, width: 2.0, depth: 0.72 };   // B's graybox table, same size
export const alchemyDoor = { x: 0, z: -3.0 };   // walk-in point that opens the AlchemyRoom scene

// ------------------------------------------------------------------ C: return-to-village sorting corner
// Eli-0731's batch2 corner placements (Blender x, y, z -> zone x, -y, height z).
const cBlender = { C01: [-0.91, 0.48, 0], C02: [0, 0.46, 0], C03: [-0.31, 0.45, 0.66], C04: [0.3, 0.4, 0.66],
  C05: [0.85, 0.52, 0], C06: [-0.43, -0.89, 0], C07: [0.84, -0.53, 0], C08: [-0.43, -0.89, 0.45] };
export const returnLayout = Object.entries(cBlender).map(([id, [x, y, h]]) => ({ id, x, z: -y, y: h, rot: 0 }));
export const returnTable = { x: 0, z: -1.3 };   // where the player stands to sort samples
