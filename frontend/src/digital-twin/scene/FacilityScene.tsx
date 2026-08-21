/* ── FacilityScene — orchestrates all 3D sub-scenes ── */
import { useRef } from 'react';
import { OrbitControls } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { Ground } from '@/digital-twin/objects/Ground';
import { WarehouseBuilding } from '@/digital-twin/objects/WarehouseBuilding';
import { DockWall } from '@/digital-twin/objects/DockWall';
import { ParkingArea } from '@/digital-twin/objects/ParkingArea';
import { TruckObject } from '@/digital-twin/objects/TruckObject';
import { RoadNetwork } from '@/digital-twin/objects/RoadNetwork';
import { GateObject } from '@/digital-twin/objects/GateObject';
import { AisleObject } from '@/digital-twin/objects/AisleObject';
import { ForkliftObject } from '@/digital-twin/objects/ForkliftObject';
import { ShipmentRoutes } from '@/digital-twin/objects/ShipmentRoutes';
import { ExceptionMarkers } from '@/digital-twin/objects/ExceptionMarkers';

// Camera view presets — keep aligned with SITE in @/constants.
const VIEWS: Record<string, { pos: [number, number, number]; target: [number, number, number] }> = {
  overview: { pos: [-34, 46, 62], target: [8, 0, 0] },
  yard: { pos: [-46, 26, 34], target: [-14, 0, 0] },
  warehouse: { pos: [26, 34, 52], target: [30, 0, -2] },
  aisle: { pos: [18, 14, 24], target: [30, 2, -4] },
  bay: { pos: [18, 10, 16], target: [30, 3, -8] },
};

export function FacilityScene() {
  const trucks = useDataStore((s) => s.trucks);
  const aisles = useDataStore((s) => s.aisles);
  const forklifts = useDataStore((s) => s.forklifts);
  const cameraView = useUIStore((s) => s.cameraView);
  const cameraTarget = useUIStore((s) => s.cameraTarget);
  const setSelected = useUIStore((s) => s.setSelected);
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const { camera } = useThree();

  // Smooth camera transitions
  useFrame(() => {
    const preset = VIEWS[cameraView] || VIEWS.overview;
    const targetPos = cameraTarget
      ? new THREE.Vector3(cameraTarget[0] - 16, cameraTarget[1] + 14, cameraTarget[2] + 18)
      : new THREE.Vector3(...preset.pos);
    const targetLook = cameraTarget
      ? new THREE.Vector3(...cameraTarget)
      : new THREE.Vector3(...preset.target);

    camera.position.lerp(targetPos, 0.045);
    if (controlsRef.current) {
      controlsRef.current.target.lerp(targetLook, 0.045);
      controlsRef.current.update();
    }
  });

  return (
    <>
      {/* ── Lighting: bright enough to actually read the facility ── */}
      <ambientLight intensity={0.75} color="#cfd8ea" />
      <hemisphereLight args={['#dce6ff', '#2a2f3d', 0.85]} />
      <directionalLight
        position={[-40, 60, 40]}
        intensity={1.5}
        color="#ffffff"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-90}
        shadow-camera-right={90}
        shadow-camera-top={90}
        shadow-camera-bottom={-90}
        shadow-camera-far={200}
      />
      <directionalLight position={[50, 40, -30]} intensity={0.5} color="#9fb4d8" />

      {/* Interior fill so racking does not fall into shadow */}
      <pointLight position={[30, 9, 0]} intensity={0.9} color="#dbe7ff" distance={70} decay={1.6} />
      <pointLight position={[16, 8, -14]} intensity={0.55} color="#cfe0ff" distance={50} decay={1.6} />
      {/* Cyan rim on the dock face for the control-room feel */}
      <pointLight position={[4, 7, 0]} intensity={0.7} color="#00d4ff" distance={55} decay={1.8} />

      <OrbitControls
        ref={controlsRef}
        enableDamping
        dampingFactor={0.08}
        minDistance={14}
        maxDistance={170}
        maxPolarAngle={Math.PI * 0.47}
        makeDefault
      />

      {/* Clicking empty space clears the selection */}
      <mesh
        position={[0, -0.5, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        onClick={() => setSelected(null)}
      >
        <planeGeometry args={[400, 400]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>

      <Ground />
      <RoadNetwork />
      <GateObject />
      <WarehouseBuilding />
      <DockWall />
      <ParkingArea />

      {trucks.map((t) => (
        <TruckObject key={t.id} truck={t} />
      ))}

      {aisles.map((a) => (
        <AisleObject key={a.id} aisle={a} />
      ))}

      {forklifts.map((f) => (
        <ForkliftObject key={f.id} forklift={f} />
      ))}

      <ShipmentRoutes />
      <ExceptionMarkers />
    </>
  );
}
