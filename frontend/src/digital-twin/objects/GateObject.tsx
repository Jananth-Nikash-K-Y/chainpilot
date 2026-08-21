/* ── GateObject — site entrance: booth, barrier and gantry ── */
import { COLORS, SITE } from '@/constants';

export function GateObject() {
  const { x, z } = SITE.gate;

  return (
    <group position={[x, 0, z]}>
      {/* Gantry posts */}
      {[-5.5, 5.5].map((dz) => (
        <mesh key={dz} position={[0, 3, z + dz]} castShadow>
          <cylinderGeometry args={[0.28, 0.28, 6, 10]} />
          <meshStandardMaterial color="#39394d" roughness={0.6} metalness={0.4} />
        </mesh>
      ))}

      {/* Gantry beam */}
      <mesh position={[0, 6, 0]} castShadow>
        <boxGeometry args={[0.5, 0.5, 11.5]} />
        <meshStandardMaterial color="#39394d" roughness={0.6} metalness={0.4} />
      </mesh>

      {/* Beam status strip */}
      <mesh position={[0.3, 6, 0]}>
        <boxGeometry args={[0.08, 0.22, 10.5]} />
        <meshStandardMaterial
          color={COLORS.cyan}
          emissive={COLORS.cyan}
          emissiveIntensity={1.1}
        />
      </mesh>

      {/* Guard booth */}
      <mesh position={[0, 1.6, -8.5]} castShadow>
        <boxGeometry args={[3.2, 3.2, 3.2]} />
        <meshStandardMaterial color="#22222f" roughness={0.75} />
      </mesh>
      <mesh position={[0, 2.2, -6.85]}>
        <planeGeometry args={[2.2, 1.2]} />
        <meshStandardMaterial
          color={COLORS.cyan}
          emissive={COLORS.cyan}
          emissiveIntensity={0.5}
          transparent
          opacity={0.65}
        />
      </mesh>

      {/* Raised barrier arm */}
      <mesh position={[1.2, 2.4, -4.4]} rotation={[0, 0, Math.PI / 3]} castShadow>
        <boxGeometry args={[0.16, 5, 0.3]} />
        <meshStandardMaterial
          color={COLORS.amber}
          emissive={COLORS.amber}
          emissiveIntensity={0.35}
        />
      </mesh>
    </group>
  );
}
