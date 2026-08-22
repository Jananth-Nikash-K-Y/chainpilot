/* ── RoadNetwork — access road from the gate to the dock apron ── */
import { useMemo } from 'react';
import { SITE } from '@/constants';
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
  const roadLength = SITE.apron.x - SITE.gate.x + 8;
  const roadCx = (SITE.gate.x + SITE.apron.x) / 2;

  const dashes = useMemo(
    () => Array.from({ length: 14 }, (_, i) => SITE.gate.x + 5 + i * 3.2),
    [],
  );

  return (
    <group>
      {/* Main approach: gate → apron */}
      <Road position={[roadCx, 0.012, 0]} size={[roadLength, 9]} color={c.road} />

      {/* Apron feeder running north–south in front of the docks */}
      <Road position={[SITE.apron.x - 3, 0.012, 0]} size={[12, 50]} color={c.road} />

      {/* Centre line dashes */}
      {dashes.map((x) => (
        <mesh key={x} position={[x, 0.03, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[1.7, 0.2]} />
          <meshBasicMaterial color={c.label} transparent opacity={0.5} />
        </mesh>
      ))}
    </group>
  );
}
