/* ── ExceptionMarkers — floating pins over whatever is going wrong ── */
import { useRef } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import type * as THREE from 'three';
import type { OperationalException } from '@/types/types';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { severityColor } from '@/constants';

function Marker({ exc }: { exc: OperationalException }) {
  const ref = useRef<THREE.Group>(null);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const hovered = useUIStore((s) => s.hoveredObject);

  const color = severityColor(exc.severity);
  const urgent = exc.severity === 'CRITICAL' || exc.severity === 'HIGH';
  const isHovered = hovered?.type === 'exception' && hovered.id === exc.id;

  // Bob gently; urgent ones bob faster so the eye catches them.
  useFrame((state) => {
    if (!ref.current) return;
    const t = state.clock.elapsedTime * (urgent ? 2.4 : 1.2) + exc.id;
    ref.current.position.y = exc.position_y + 3 + Math.sin(t) * 0.4;
    ref.current.rotation.y = state.clock.elapsedTime * 0.6;
  });

  const identity = { type: 'exception' as const, id: exc.id, code: exc.code };

  return (
    <group position={[exc.position_x, exc.position_y, exc.position_z]}>
      {/* Ground halo */}
      <mesh position={[0, 0.05, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.4, 1.9, 32]} />
        <meshBasicMaterial color={color} transparent opacity={0.45} />
      </mesh>

      {/* Tether */}
      <mesh position={[0, 1.6, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 3.2, 6]} />
        <meshBasicMaterial color={color} transparent opacity={0.4} />
      </mesh>

      <group
        ref={ref}
        onClick={(e) => {
          e.stopPropagation();
          setSelected(identity);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(identity);
        }}
        onPointerOut={() => setHovered(null)}
      >
        <mesh castShadow>
          <octahedronGeometry args={[urgent ? 0.85 : 0.6, 0]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={urgent ? 1.6 : 0.8}
            roughness={0.3}
          />
        </mesh>

        {isHovered && (
          <Html position={[0, 1.6, 0]} center distanceFactor={45}>
            <div className="object-tooltip">
              <div className="tooltip-code">
                {exc.code} · {exc.severity}
              </div>
              <div className="tooltip-status">{exc.title}</div>
            </div>
          </Html>
        )}
      </group>
    </group>
  );
}

export function ExceptionMarkers() {
  const exceptions = useDataStore((s) => s.exceptions);

  return (
    <group>
      {exceptions
        .filter((e) => !e.resolved)
        .map((e) => (
          <Marker key={e.id} exc={e} />
        ))}
    </group>
  );
}
