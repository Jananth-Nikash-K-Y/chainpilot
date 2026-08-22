/* ── FacilityScene — orchestrates all 3D sub-scenes ── */
import { useEffect, useRef } from 'react';
import { OrbitControls } from '@react-three/drei';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { useSceneColors } from '@/hooks';
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

/** Distance below which a preset fly-to is considered finished. */
const ARRIVED = 1.2;

export function FacilityScene() {
  const trucks = useDataStore((s) => s.trucks);
  const aisles = useDataStore((s) => s.aisles);
  const forklifts = useDataStore((s) => s.forklifts);
  const cameraView = useUIStore((s) => s.cameraView);
  const cameraTarget = useUIStore((s) => s.cameraTarget);
  const cameraDistance = useUIStore((s) => s.cameraDistance);
  const setSelected = useUIStore((s) => s.setSelected);
  const colors = useSceneColors();

  const controlsRef = useRef<OrbitControlsImpl>(null);
  const { camera } = useThree();

  // The camera only animates while flying to a preset. Once it arrives — or
  // the moment the user grabs the controls — animation stops and OrbitControls
  // owns the camera completely. Previously this lerped every frame, which
  // fought every drag and made the scene feel locked.
  const flying = useRef(true);

  useEffect(() => {
    // A new preset (or a newly focused object) restarts the fly-to.
    flying.current = true;
  }, [cameraView, cameraTarget, cameraDistance]);

  useFrame(() => {
    if (!flying.current) return;

    const preset = VIEWS[cameraView] ?? VIEWS.overview;
    // Standoff scales with the focus distance, so focusing a bay puts the
    // camera inside the aisle rather than hovering above the building.
    const d = cameraDistance ?? 27;
    const destPos = cameraTarget
      ? new THREE.Vector3(
          cameraTarget[0] - d * 0.6,
          cameraTarget[1] + d * 0.5,
          cameraTarget[2] + d * 0.66,
        )
      : new THREE.Vector3(...preset.pos);
    const destLook = cameraTarget
      ? new THREE.Vector3(...cameraTarget)
      : new THREE.Vector3(...preset.target);

    camera.position.lerp(destPos, 0.08);
    const controls = controlsRef.current;
    if (controls) {
      controls.target.lerp(destLook, 0.08);
      controls.update();
      // Scale the arrival threshold with the trip, so short hops into a bay
      // settle as crisply as long ones across the site.
      if (camera.position.distanceTo(destPos) < Math.max(ARRIVED, d * 0.05)) {
        flying.current = false;
      }
    }
  });

  return (
    <>
      {/* ── Lighting ── */}
      <ambientLight intensity={colors.ambient} color="#ffffff" />
      <hemisphereLight args={['#ffffff', colors.floor, colors.hemi]} />
      <directionalLight
        position={[-40, 60, 40]}
        intensity={colors.sun}
        color="#ffffff"
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-left={-90}
        shadow-camera-right={90}
        shadow-camera-top={90}
        shadow-camera-bottom={-90}
        shadow-camera-far={220}
      />
      <directionalLight position={[50, 40, -30]} intensity={colors.fill * 0.6} color="#c9d6ee" />
      <pointLight position={[30, 9, 0]} intensity={colors.fill} distance={80} decay={1.6} />
      <pointLight position={[16, 8, -14]} intensity={colors.fill * 0.7} distance={55} decay={1.6} />

      {/* ── Camera controls: free enough to walk into a single bay ── */}
      <OrbitControls
        ref={controlsRef}
        makeDefault
        enableDamping
        dampingFactor={0.06}
        enablePan
        // Pan across the ground plane rather than the screen plane, so
        // dragging moves you through the site the way you expect.
        screenSpacePanning={false}
        panSpeed={1.1}
        rotateSpeed={0.9}
        zoomSpeed={1.2}
        // 1.2 lets the camera sit between two racking faces; 400 pulls back
        // far enough to see the whole site plus inbound routes.
        minDistance={1.2}
        maxDistance={400}
        // Zoom toward the cursor — the difference between orbiting around a
        // fixed point and actually navigating into an aisle.
        zoomToCursor
        // Just shy of the horizon, so you can drop to eye level inside the
        // building without flipping under the floor.
        maxPolarAngle={Math.PI * 0.499}
        minPolarAngle={0.02}
        // Any user input cancels the automatic fly-to immediately.
        onStart={() => {
          flying.current = false;
        }}
      />

      {/* Clicking empty space clears the selection */}
      <mesh
        position={[0, -0.5, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        onClick={() => setSelected(null)}
      >
        <planeGeometry args={[500, 500]} />
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
