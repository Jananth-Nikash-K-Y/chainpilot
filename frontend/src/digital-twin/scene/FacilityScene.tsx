/* ── FacilityScene — orchestrates all 3D sub-scenes ── */
import { useRef } from 'react';
import { OrbitControls } from '@react-three/drei';
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

// Camera view presets
const VIEWS: Record<string, { pos: [number, number, number]; target: [number, number, number] }> = {
  overview: { pos: [80, 60, 80], target: [0, 0, 5] },
  yard: { pos: [-40, 30, -20], target: [-20, 0, -10] },
  warehouse: { pos: [10, 25, 35], target: [10, 0, 15] },
};

export function FacilityScene() {
  const trucks = useDataStore((s) => s.trucks);
  const aisles = useDataStore((s) => s.aisles);
  const forklifts = useDataStore((s) => s.forklifts);
  const cameraView = useUIStore((s) => s.cameraView);
  const cameraTarget = useUIStore((s) => s.cameraTarget);
  const controlsRef = useRef<any>(null);
  const { camera } = useThree();

  // Smooth camera transitions
  useFrame(() => {
    const preset = VIEWS[cameraView] || VIEWS.overview;
    const targetPos = cameraTarget
      ? new THREE.Vector3(cameraTarget[0] + 8, cameraTarget[1] + 12, cameraTarget[2] + 8)
      : new THREE.Vector3(...preset.pos);
    const targetLook = cameraTarget
      ? new THREE.Vector3(...cameraTarget)
      : new THREE.Vector3(...preset.target);

    camera.position.lerp(targetPos, 0.03);
    if (controlsRef.current) {
      controlsRef.current.target.lerp(targetLook, 0.03);
      controlsRef.current.update();
    }
  });

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.25} color="#b0c4de" />
      <directionalLight
        position={[60, 80, 40]}
        intensity={0.8}
        color="#e8edf5"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <pointLight position={[-30, 15, -20]} intensity={0.3} color="#00d4ff" distance={60} />
      <pointLight position={[20, 10, 0]} intensity={0.2} color="#3b82f6" distance={40} />

      <OrbitControls
        ref={controlsRef}
        enableDamping
        dampingFactor={0.08}
        minDistance={10}
        maxDistance={200}
        maxPolarAngle={Math.PI * 0.48}
      />

      <Ground />
      <RoadNetwork />
      <GateObject />
      <WarehouseBuilding />
      <DockWall />
      <ParkingArea />

      {/* Trucks */}
      {trucks.map((t) => (
        <TruckObject key={t.id} truck={t} />
      ))}

      {/* Warehouse aisles */}
      {aisles.map((a) => (
        <AisleObject key={a.id} aisle={a} />
      ))}

      {/* Forklifts */}
      {forklifts.map((f) => (
        <ForkliftObject key={f.id} forklift={f} />
      ))}

      <ShipmentRoutes />
      <ExceptionMarkers />
    </>
  );
}
