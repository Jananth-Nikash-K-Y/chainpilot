/* ── RoadNetwork — access road, holding lane and dock apron feeder ── */
import { useMemo } from 'react';
import { COLORS, SITE } from '@/constants';
import { useSceneColors } from '@/hooks';

function Road({
  position,
  size,
  color,
}: {
  position: [number, number, number];
  size: [number, number];
  color: string;
}) {
  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={size} />
      <meshStandardMaterial color={color} roughness={0.95} />
    </mesh>
  );
}

export function RoadNetwork() {
  const c = useSceneColors();

  const { xStart, xEnd, z, width } = SITE.road;
  const roadLength = xEnd - xStart;
  const roadCx = (xStart + xEnd) / 2;

  // Centre line separating inbound (north) from outbound (south).
  const dashes = useMemo(
    () => Array.from({ length: Math.floor(roadLength / 4) }, (_, i) => xStart + 3 + i * 4),
    [xStart, roadLength],
  );

  return (
    <group>
      {/* Main two-way approach: gate → apron */}
      <Road position={[roadCx, 0.012, z]} size={[roadLength, width]} color={c.road} />

      {/* Holding lane, parallel and clear of the running lanes */}
      <Road position={[roadCx, 0.012, -14]} size={[roadLength, 7]} color={c.road} />

      {/* Shoulder for held vehicles */}
      <Road position={[roadCx, 0.012, -22]} size={[roadLength, 7]} color={c.road} />

      {/* Apron feeder in front of the docks, joining the road */}
      <Road position={[SITE.apron.x - 4, 0.012, 0]} size={[14, 52]} color={c.apron} />

      {/* Centre line */}
      {dashes.map((x) => (
        <mesh key={x} position={[x, 0.03, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[2, 0.22]} />
          <meshBasicMaterial color={COLORS.amber} transparent opacity={0.55} />
        </mesh>
      ))}

      {/* Lane edge lines */}
      {[z - width / 2 + 0.4, z + width / 2 - 0.4].map((lz) => (
        <mesh key={lz} position={[roadCx, 0.03, lz]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[roadLength, 0.16]} />
          <meshBasicMaterial color={c.label} transparent opacity={0.4} />
        </mesh>
      ))}
    </group>
  );
}
