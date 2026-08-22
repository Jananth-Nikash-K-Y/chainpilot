/* ── DockWall — the loading face of the warehouse plus one door per dock ── */
import { Text } from '@react-three/drei';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { COLORS, SITE, colorFor, dockZ } from '@/constants';
import { useSceneColors } from '@/hooks';

const DOOR_W = 3.4;
const DOOR_H = 4.6;

export function DockWall() {
  const c = useSceneColors();
  const docks = useDataStore((s) => s.docks);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const selected = useUIStore((s) => s.selectedObject);

  const { x, zMin, zMax, height } = SITE.dockWall;
  const length = zMax - zMin;
  const cz = (zMin + zMax) / 2;

  return (
    <group>
      {/* Wall face */}
      <mesh position={[x, height / 2, cz]} castShadow receiveShadow>
        <boxGeometry args={[0.7, height, length]} />
        <meshStandardMaterial color={c.wall} roughness={0.8} metalness={0.15} />
      </mesh>

      {/* Concrete apron the trucks reverse onto */}
      <mesh position={[x - 7, 0.02, cz]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[length, 14]} />
        <meshStandardMaterial color={c.apron} roughness={0.93} />
      </mesh>

      {docks.map((d) => {
        const z = dockZ(d.position_index);
        const color = colorFor(d.status);
        const isSelected = selected?.type === 'dock' && selected.id === d.id;
        const identity = { type: 'dock' as const, id: d.id, code: d.code };

        return (
          <group key={d.id} position={[x - 0.4, 0, z]}>
            {/* Door recess */}
            <mesh position={[0, DOOR_H / 2, 0]}>
              <boxGeometry args={[0.12, DOOR_H + 0.4, DOOR_W + 0.4]} />
              <meshStandardMaterial color={c.lane} roughness={0.9} />
            </mesh>

            {/* Roller shutter, tinted by dock status */}
            <mesh
              position={[-0.12, DOOR_H / 2, 0]}
              castShadow
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
              <boxGeometry args={[0.22, DOOR_H, DOOR_W]} />
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={isSelected ? 1.0 : 0.4}
                roughness={0.45}
                metalness={0.3}
              />
            </mesh>

            {/* Shutter slats */}
            {Array.from({ length: 6 }, (_, i) => (
              <mesh key={i} position={[-0.25, 0.5 + i * 0.72, 0]}>
                <boxGeometry args={[0.04, 0.06, DOOR_W * 0.94]} />
                <meshBasicMaterial color="#1a1e29" transparent opacity={0.45} />
              </mesh>
            ))}

            {/* Status beacon above the door */}
            <mesh position={[-0.3, DOOR_H + 0.7, 0]}>
              <sphereGeometry args={[0.24, 14, 14]} />
              <meshStandardMaterial color={color} emissive={color} emissiveIntensity={1.8} />
            </mesh>

            {/* Dock code stencilled on the wall */}
            <Text
              position={[-0.32, DOOR_H + 1.6, 0]}
              rotation={[0, -Math.PI / 2, 0]}
              fontSize={0.78}
              color={isSelected ? COLORS.cyan : c.label}
              anchorX="center"
              anchorY="middle"
            >
              {d.code}
            </Text>

            {/* Berth guide lines on the apron */}
            {[-DOOR_W / 2, DOOR_W / 2].map((dz) => (
              <mesh
                key={dz}
                position={[-6, 0.04, dz]}
                rotation={[-Math.PI / 2, 0, 0]}
              >
                <planeGeometry args={[11, 0.14]} />
                <meshBasicMaterial color={COLORS.amber} transparent opacity={0.4} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}
