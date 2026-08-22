/* ── WarehouseBuilding — open-roof shell so the interior stays readable ── */
import { useMemo } from 'react';
import { SITE } from '@/constants';
import { useSceneColors } from '@/hooks';

export function WarehouseBuilding() {
  const c = useSceneColors();
  const { xMin, xMax, zMin, zMax, height } = SITE.warehouse;

  const width = xMax - xMin;
  const depth = zMax - zMin;
  const cx = (xMin + xMax) / 2;
  const cz = (zMin + zMax) / 2;

  // Roof trusses spanning the width, spaced along the depth.
  const trusses = useMemo(
    () => Array.from({ length: 11 }, (_, i) => zMin + 2 + i * ((depth - 4) / 10)),
    [zMin, depth],
  );

  return (
    <group>
      {/* Floor slab — light enough that racking and forklifts read against it */}
      <mesh position={[cx, 0.02, cz]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[width, depth]} />
        <meshStandardMaterial color={c.floor} roughness={0.88} metalness={0.04} />
      </mesh>

      {/* Back and side walls (the dock face is handled by DockWall) */}
      <mesh position={[xMax, height / 2, cz]} castShadow receiveShadow>
        <boxGeometry args={[0.5, height, depth]} />
        <meshStandardMaterial color={c.wall} roughness={0.8} metalness={0.12} />
      </mesh>
      {[zMin, zMax].map((z) => (
        <mesh key={z} position={[cx, height / 2, z]} castShadow receiveShadow>
          <boxGeometry args={[width, height, 0.5]} />
          <meshStandardMaterial
            color={c.wall}
            roughness={0.8}
            metalness={0.12}
            transparent
            opacity={0.55}
          />
        </mesh>
      ))}

      {/* Corner columns */}
      {[
        [xMin, zMin],
        [xMin, zMax],
        [xMax, zMin],
        [xMax, zMax],
      ].map(([x, z]) => (
        <mesh key={`${x}-${z}`} position={[x, height / 2, z]} castShadow>
          <boxGeometry args={[0.9, height, 0.9]} />
          <meshStandardMaterial color={c.frame} roughness={0.5} metalness={0.5} />
        </mesh>
      ))}

      {/* Roof trusses — open so the camera sees inside */}
      {trusses.map((z) => (
        <group key={z}>
          <mesh position={[cx, height - 0.3, z]} castShadow>
            <boxGeometry args={[width, 0.22, 0.22]} />
            <meshStandardMaterial color={c.frame} roughness={0.5} metalness={0.5} />
          </mesh>
          {/* Truss webbing */}
          <mesh position={[cx, height - 0.95, z]}>
            <boxGeometry args={[width, 0.08, 0.08]} />
            <meshStandardMaterial color={c.frame} roughness={0.6} metalness={0.4} />
          </mesh>
        </group>
      ))}

      {/* Eave beams */}
      {[zMin, zMax].map((z) => (
        <mesh key={`eave-${z}`} position={[cx, height, z]}>
          <boxGeometry args={[width, 0.35, 0.35]} />
          <meshStandardMaterial color={c.frame} roughness={0.45} metalness={0.55} />
        </mesh>
      ))}
    </group>
  );
}
