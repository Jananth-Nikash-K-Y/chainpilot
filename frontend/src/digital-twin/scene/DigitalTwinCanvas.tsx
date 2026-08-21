/* ── Digital Twin Canvas — React Three Fiber entry point ── */
import { Canvas } from '@react-three/fiber';
import { FacilityScene } from './FacilityScene';

export function DigitalTwinCanvas() {
  return (
    <Canvas
      camera={{ position: [80, 60, 80], fov: 50, near: 0.1, far: 500 }}
      style={{ position: 'absolute', inset: 0 }}
      gl={{ antialias: true, alpha: false }}
      dpr={[1, 2]}
    >
      <color attach="background" args={['#08080e']} />
      <fog attach="fog" args={['#08080e', 80, 250]} />
      <FacilityScene />
    </Canvas>
  );
}
