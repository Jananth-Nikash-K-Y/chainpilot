/* ── Ground — site slab with a subtle grid overlay ── */
import { Grid } from '@react-three/drei';
import { SITE } from '@/constants';
import { useSceneColors } from '@/hooks';

export function Ground() {
  const c = useSceneColors();

  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.03, 0]} receiveShadow>
        <planeGeometry args={[SITE.ground.size, SITE.ground.size]} />
        <meshStandardMaterial color={c.yard} roughness={0.95} metalness={0.03} />
      </mesh>

      <Grid
        position={[0, -0.01, 0]}
        args={[SITE.ground.size, SITE.ground.size]}
        cellSize={4}
        cellThickness={0.5}
        cellColor={c.grid}
        sectionSize={20}
        sectionThickness={1}
        sectionColor={c.gridSection}
        fadeDistance={165}
        fadeStrength={1.2}
        followCamera={false}
        infiniteGrid={false}
      />
    </group>
  );
}
