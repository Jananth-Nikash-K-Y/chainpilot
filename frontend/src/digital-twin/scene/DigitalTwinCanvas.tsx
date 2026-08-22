/* ── Digital Twin Canvas — React Three Fiber entry point ── */
import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { useSceneColors } from '@/hooks';
import { FacilityScene } from './FacilityScene';

export function DigitalTwinCanvas() {
  const colors = useSceneColors();

  return (
    <Canvas
      camera={{ position: [-34, 46, 62], fov: 45, near: 0.1, far: 900 }}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: false }}
      shadows
      dpr={[1, 2]}
    >
      <color attach="background" args={[colors.background]} />
      <fog attach="fog" args={[colors.fog, 190, 460]} />
      <Suspense fallback={null}>
        <FacilityScene />
      </Suspense>
    </Canvas>
  );
}
