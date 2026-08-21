/* ── ParkingArea — the waiting yard, one pad per parking slot ── */
import { Text } from '@react-three/drei';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { COLORS, MATERIAL, SITE, colorFor, parkingPosition } from '@/constants';

export function ParkingArea() {
  const slots = useDataStore((s) => s.parkingSlots);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const selected = useUIStore((s) => s.selectedObject);

  const { xStart, zStart, cols, rows, padW, padD, gapX, gapZ } = SITE.parking;
  const spanX = cols * (padW + gapX);
  const spanZ = rows * (padD + gapZ);

  return (
    <group>
      {/* Yard surface */}
      <mesh
        position={[xStart + spanX / 2 - padW / 2 - gapX / 2, 0.01, zStart + spanZ / 2 - padD / 2 - gapZ / 2]}
        rotation={[-Math.PI / 2, 0, 0]}
        receiveShadow
      >
        <planeGeometry args={[spanX + 4, spanZ + 4]} />
        <meshStandardMaterial color={MATERIAL.apron} roughness={0.94} />
      </mesh>

      {slots.map((s) => {
        const [x, z] = parkingPosition(s.position_index);
        const occupied = s.status === 'OCCUPIED';
        const color = colorFor(s.status);
        const isSelected = selected?.type === 'parking' && selected.id === s.id;
        const identity = { type: 'parking' as const, id: s.id, code: s.code };

        return (
          <group key={s.id} position={[x, 0, z]}>
            {/* Painted bay */}
            <mesh
              position={[0, 0.03, 0]}
              rotation={[-Math.PI / 2, 0, 0]}
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
              <planeGeometry args={[padW, padD]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={isSelected ? 0.5 : 0.12}
                transparent
                opacity={s.status === 'AVAILABLE' ? 0.16 : 0.34}
                roughness={0.9}
              />
            </mesh>

            {/* Bay outline */}
            {[-padW / 2, padW / 2].map((dx) => (
              <mesh key={dx} position={[dx, 0.04, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <planeGeometry args={[0.12, padD]} />
                <meshBasicMaterial color="#c9d3e6" transparent opacity={0.45} />
              </mesh>
            ))}

            {/* Parked trailer */}
            {occupied && (
              <group>
                <mesh position={[0, 1.5, 0]} castShadow>
                  <boxGeometry args={[2.3, 2.8, 5.2]} />
                  <meshStandardMaterial color="#7c869e" roughness={0.65} metalness={0.25} />
                </mesh>
                {/* Landing gear */}
                <mesh position={[0, 0.35, 2]}>
                  <boxGeometry args={[1.6, 0.7, 0.2]} />
                  <meshStandardMaterial color="#4a5266" metalness={0.5} />
                </mesh>
              </group>
            )}

            <Text
              position={[0, 0.05, padD / 2 - 0.6]}
              rotation={[-Math.PI / 2, 0, 0]}
              fontSize={0.62}
              color={COLORS.slate}
              anchorX="center"
              anchorY="middle"
            >
              {s.code}
            </Text>
          </group>
        );
      })}
    </group>
  );
}
