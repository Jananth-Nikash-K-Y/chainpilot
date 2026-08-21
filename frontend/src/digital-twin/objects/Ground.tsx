/* ── Ground — site slab with a subtle grid overlay ── */
import { Grid } from '@react-three/drei';
import { MATERIAL, SITE } from '@/constants';

export function Ground() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.03, 0]} receiveShadow>
        <planeGeometry args={[SITE.ground.size, SITE.ground.size]} />
        <meshStandardMaterial color={MATERIAL.yard} roughness={0.95} metalness={0.03} />
      </mesh>

      <Grid
        position={[0, -0.01, 0]}
        args={[SITE.ground.size, SITE.ground.size]}
        cellSize={4}
        cellThickness={0.5}
        cellColor="#454c5e"
        sectionSize={20}
        sectionThickness={1}
        sectionColor="#5b6a8a"
        fadeDistance={165}
        fadeStrength={1.2}
        followCamera={false}
        infiniteGrid={false}
      />
    </group>
  );
}
