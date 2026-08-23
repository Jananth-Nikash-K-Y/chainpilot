/* ── TruckObject — one tractor + trailer, positioned from backend state ── */
import { useRef } from 'react';
import { Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import type * as THREE from 'three';
import type { Truck } from '@/types/types';
import { useUIStore } from '@/stores/uiStore';
import { COLORS, colorFor } from '@/constants';

interface Props {
  truck: Truck;
}

export function TruckObject({ truck }: Props) {
  const groupRef = useRef<THREE.Group>(null);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const hovered = useUIStore((s) => s.hoveredObject);
  const selected = useUIStore((s) => s.selectedObject);

  const isHovered = hovered?.type === 'truck' && hovered.id === truck.id;
  const isSelected = selected?.type === 'truck' && selected.id === truck.id;
  const color = colorFor(truck.status);

  // Arriving trucks idle rather than drive down the lane.
  //
  // The previous version advanced each truck independently and snapped it back
  // to its own start on passing x=4. Because every truck reset at a different
  // moment, the seeded 15-unit queue spacing collapsed — a follower ended up
  // 6 units behind a truck 10.1 long, so trailers intersected. It also drove
  // them through x=4, which is exactly where berthed trucks stand.
  //
  // Spacing can only be preserved by moving the whole convoy in lockstep, and
  // a single truck cannot know how many others share its lane. So the motion
  // here is a small in-place shudder that cannot close a gap.
  const idling = truck.status === 'ARRIVING' || truck.status === 'WAITING';
  useFrame((state) => {
    if (!idling || !groupRef.current) return;
    const t = state.clock.elapsedTime * 9 + truck.id;
    groupRef.current.position.y = truck.position_y + Math.sin(t) * 0.02;
  });

  const identity = { type: 'truck' as const, id: truck.id, code: truck.code };

  return (
    <group
      ref={groupRef}
      position={[truck.position_x, truck.position_y, truck.position_z]}
      rotation={[0, truck.rotation_y, 0]}
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
      {/* Trailer */}
      <mesh position={[-2.6, 1.9, 0]} castShadow>
        <boxGeometry args={[7.2, 3, 2.6]} />
        <meshStandardMaterial
          color="#2e2e40"
          roughness={0.65}
          metalness={0.25}
          emissive={isSelected ? color : '#000000'}
          emissiveIntensity={isSelected ? 0.25 : 0}
        />
      </mesh>

      {/* Load-level strip on the trailer flank */}
      <mesh position={[-2.6 - (7.2 * (1 - truck.load_pct / 100)) / 2, 0.55, 1.34]}>
        <planeGeometry args={[(7.2 * truck.load_pct) / 100, 0.3]} />
        <meshBasicMaterial color={color} transparent opacity={0.85} />
      </mesh>

      {/* Tractor unit */}
      <mesh position={[2.1, 1.5, 0]} castShadow>
        <boxGeometry args={[2.8, 2.4, 2.5]} />
        <meshStandardMaterial color={color} roughness={0.5} metalness={0.3} />
      </mesh>

      {/* Windscreen */}
      <mesh position={[3.45, 2.0, 0]}>
        <planeGeometry args={[1.4, 1.0]} />
        <meshStandardMaterial color="#0d1520" roughness={0.2} metalness={0.6} />
      </mesh>

      {/* Wheels */}
      {[
        [2.4, -1.35],
        [2.4, 1.35],
        [-0.6, -1.35],
        [-0.6, 1.35],
        [-4.6, -1.35],
        [-4.6, 1.35],
      ].map(([wx, wz], i) => (
        <mesh key={i} position={[wx, 0.55, wz]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.55, 0.55, 0.35, 12]} />
          <meshStandardMaterial color="#0e0e14" roughness={0.9} />
        </mesh>
      ))}

      {/* Risk beacon */}
      {(truck.risk === 'HIGH' || truck.risk === 'CRITICAL') && (
        <mesh position={[2.1, 3.1, 0]}>
          <sphereGeometry args={[0.28, 12, 12]} />
          <meshStandardMaterial
            color={COLORS.red}
            emissive={COLORS.red}
            emissiveIntensity={2}
          />
        </mesh>
      )}

      {/* Selection ring */}
      {isSelected && (
        <mesh position={[-1, 0.06, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[5.4, 5.9, 40]} />
          <meshBasicMaterial color={COLORS.cyan} transparent opacity={0.8} />
        </mesh>
      )}

      {isHovered && (
        <Html position={[0, 4.4, 0]} center distanceFactor={40} zIndexRange={[20, 0]}>
          <div className="object-tooltip">
            <div className="tooltip-code">{truck.code}</div>
            <div className="tooltip-status">
              {truck.status}
              {truck.dock_code ? ` · ${truck.dock_code}` : ''}
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}
