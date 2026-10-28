// Small reusable dirt blocks, based on the saved winding-road three-view.
// The meadow remains a separate surface and can receive its own patch blocks.
export const roadRoute = [
  [-.2, 1], [-1.2, -.6], [-2.5, -1.8], [-3.6, -3.2], [-4.1, -4.9],
  [-4.35, -6.7], [-4.4, -8.5],
];
const edgeShapes = [
  { left: [0, .29, -.16, .32, 0], right: [0, -.25, .18, -.27, 0] },
  { left: [0, -.24, .33, -.18, 0], right: [0, .24, -.32, .21, 0] },
  { left: [0, .34, -.17, .20, 0], right: [0, -.19, .29, -.31, 0] },
];
export function makeRoadBlocks() {
  const normalAt = vertex => {
    const before = roadRoute[Math.max(0, vertex - 1)];
    const after = roadRoute[Math.min(roadRoute.length - 1, vertex + 1)];
    const dx = after[0] - before[0], dz = after[1] - before[1];
    const length = Math.hypot(dx, dz);
    return [-dz / length, dx / length];
  };
  const halfWidthAt = vertex => 1.24 + .18 * Math.sin(vertex * 1.73);
  return roadRoute.slice(0, -1).map((start, index) => {
    const end = roadRoute[index + 1];
    const dx = end[0] - start[0], dz = end[1] - start[1];
    const length = Math.hypot(dx, dz);
    const normalStart = normalAt(index), normalEnd = normalAt(index + 1);
    const shape = edgeShapes[index % edgeShapes.length];
    const stations = Array.from({ length: 5 }, (_, step) => {
      const t = step / 4, cx = start[0] + dx * t, cz = start[1] + dz * t;
      const nx = normalStart[0] * (1 - t) + normalEnd[0] * t;
      const nz = normalStart[1] * (1 - t) + normalEnd[1] * t;
      const half = halfWidthAt(index) * (1 - t) + halfWidthAt(index + 1) * t;
      const leftWidth = half + shape.left[step], rightWidth = half + shape.right[step];
      return {
        left: [cx + nx * leftWidth, .26, cz + nz * leftWidth],
        right: [cx - nx * rightWidth, .26, cz - nz * rightWidth],
        textureV: t * length / 2,
      };
    });
    return { variant: index % edgeShapes.length, stations };
  });
}
export const meadowBlocks = [
  { x: 1.9, z: -1.5, radius: 1.7, variant: 2 },
  { x: -1.4, z: -5.5, radius: 1.4, variant: 1 },
  { x: -6.4, z: -5.8, radius: 1.5, variant: 0 },
];

// A shallow, continuous verge follows the old road's left edge. Six small
// pieces share end positions; no individual disk cuts a pointed bite into it.
export function makeLeftVergeBlocks() {
  const edge = z => -.52 + .38 * Math.sin((15 - z) * 1.15) + .04 * Math.sin((15 - z) * 2.0);
  return Array.from({ length: 6 }, (_, block) => {
    const stations = Array.from({ length: 9 }, (_, step) => {
      const z = 15 - block * 2 - step * .25;
      return { left: [-2.7, .27, z], right: [edge(z), .27, z], textureV: z / 5 };
    });
    return stations;
  });
}
export function makeMeadowBlock({ x, z, radius, variant }) {
  const points = [[x, .27, z]];
  for (let i = 0; i <= 24; i++) {
    const angle = i / 24 * Math.PI * 2;
    const wobble = 1 + .065 * Math.sin(i * 1.1 + variant) + .035 * Math.cos(i * 1.7 + variant);
    points.push([x + Math.cos(angle) * radius * wobble, .27, z + Math.sin(angle) * radius * wobble]);
  }
  return points;
}
