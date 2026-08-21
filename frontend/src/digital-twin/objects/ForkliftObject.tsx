/* ── ForkliftObject — animated when the operator is actively moving ── */
import { useRef } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import type * as THREE from 'three';
import type { Forklift } from '@/types/types';
import { useUIStore } from '@/stores/uiStore';
import { COLORS, colorFor } from '@/constants';

interface Props {
  forklift: Forklift;
}

export function ForkliftObject({ forklift }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const hovered = useUIStore((s) => s.hoveredObject);

  const isHovered = hovered?.type === 'forklift' && hovered.id === forklift.id;
  const color = colorFor(forklift.activity);
  const isMoving = forklift.activity === 'MOVING' || forklift.activity === 'REPLENISHING';

  // Patrol up and down the aisle so activity reads at a glance.
  useFrame((state) => {
    if (!isMoving || !groupRef.current) return;
    const t = state.clock.elapsedTime * 0.5 + forklift.id;
    groupRef.current.position.z = forklift.position_z + Math.sin(t) * 5;
    groupRef.current.rotation.y = Math.cos(t) > 0 ? 0 : Math.PI;
  });

  const identity = { type: 'forklift' as const, id: forklift.id, code: forklift.code };

  return (
    <group
      ref={groupRef}
      position={[forklift.position_x, forklift.position_y, forklift.position_z]}
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
      {/* Chassis */}
      <mesh position={[0, 0.6, 0]} castShadow>
        <boxGeometry args={[1.1, 0.9, 1.7]} />
        <meshStandardMaterial color={color} roughness={0.55} metalness={0.3} />
      </mesh>

      {/* Overhead guard */}
      <mesh position={[0, 1.65, -0.2]}>
        <boxGeometry args={[1.05, 0.08, 1.1]} />
        <meshStandardMaterial color="#2b3348" metalness={0.5} roughness={0.5} />
      </mesh>
      {[
        [-0.45, -0.65],
        [0.45, -0.65],
        [-0.45, 0.25],
        [0.45, 0.25],
      ].map(([px, pz], i) => (
        <mesh key={i} position={[px, 1.15, pz]}>
          <cylinderGeometry args={[0.05, 0.05, 1, 6]} />
          <meshStandardMaterial color="#2b3348" metalness={0.5} />
        </mesh>
      ))}

      {/* Mast + forks */}
      <mesh position={[0, 1.1, 0.95]}>
        <boxGeometry args={[0.9, 2.2, 0.1]} />
        <meshStandardMaterial color="#39394d" metalness={0.5} roughness={0.5} />
      </mesh>
      {[-0.28, 0.28].map((fx) => (
        <mesh key={fx} position={[fx, 0.16, 1.35]}>
          <boxGeometry args={[0.12, 0.06, 0.85]} />
          <meshStandardMaterial color="#4a4a60" metalness={0.6} />
        </mesh>
      ))}

      {/* Wheels */}
      {[
        [-0.5, -0.55],
        [0.5, -0.55],
        [-0.5, 0.6],
        [0.5, 0.6],
      ].map(([wx, wz], i) => (
        <mesh key={i} position={[wx, 0.22, wz]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.22, 0.22, 0.16, 10]} />
          <meshStandardMaterial color="#0e0e14" roughness={0.9} />
        </mesh>
      ))}

      {/* Low-battery warning */}
      {forklift.battery_pct < 25 && (
        <mesh position={[0, 2, 0]}>
          <sphereGeometry args={[0.18, 10, 10]} />
          <meshStandardMaterial
            color={COLORS.red}
            emissive={COLORS.red}
            emissiveIntensity={2}
          />
        </mesh>
      )}

      {isHovered && (
        <Html position={[0, 2.6, 0]} center distanceFactor={40}>
          <div className="object-tooltip">
            <div className="tooltip-code">{forklift.code}</div>
            <div className="tooltip-status">
              {forklift.activity} · {forklift.battery_pct.toFixed(0)}%
              {forklift.operator ? ` · ${forklift.operator}` : ''}
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}
