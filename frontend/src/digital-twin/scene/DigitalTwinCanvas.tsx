/* ── Digital Twin Canvas — React Three Fiber entry point ── */
import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { FacilityScene } from './FacilityScene';

export function DigitalTwinCanvas() {
  return (
    <Canvas
      camera={{ position: [-34, 46, 62], fov: 45, near: 0.1, far: 600 }}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: false }}
      shadows
      dpr={[1, 2]}
    >
      <color attach="background" args={['#161a24']} />
      <fog attach="fog" args={['#161a24', 150, 320]} />
      <Suspense fallback={null}>
        <FacilityScene />
      </Suspense>
    </Canvas>
  );
}
