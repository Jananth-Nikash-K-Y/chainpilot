/* ── AisleObject — a double-sided racking run with palletised loads ── */
import { useMemo } from 'react';
import { Html, Text } from '@react-three/drei';
import type { Aisle, Bay } from '@/types/types';
import { useDataStore } from '@/stores/dataStore';
import { useUIStore } from '@/stores/uiStore';
import { COLORS, MATERIAL, SITE, colorFor } from '@/constants';

interface Props {
  aisle: Aisle;
}

const LEVELS = 3;
const LEVEL_H = 2.2;
const RACK_W = 1.5; // depth of one rack face
const UPRIGHT = 0.14;

/** One palletised load sitting on a beam. */
function PalletLoad({
  bay,
  side,
  onSelect,
  onHover,
  onOut,
  selected,
}: {
  bay: Bay;
  side: -1 | 1;
  onSelect: () => void;
  onHover: () => void;
  onOut: () => void;
  selected: boolean;
}) {
  const fill = Math.min(1, bay.current_quantity / Math.max(1, bay.capacity));
  const color = colorFor(bay.stock_status);
  const level = Math.min(LEVELS, Math.max(1, bay.level));
  const y = (level - 1) * LEVEL_H + 0.55;
  const boxH = 0.5 + fill * 1.1;
  const depth = SITE.aisle.bayDepth * 0.72;

  return (
    <group position={[side * (RACK_W / 2 + 0.1), 0, 0]}>
      {/* Pallet base */}
      <mesh position={[0, y - 0.12, 0]} castShadow>
        <boxGeometry args={[RACK_W * 0.9, 0.14, depth]} />
        <meshStandardMaterial color="#8a6a45" roughness={0.9} />
      </mesh>

      {/* Goods */}
      <mesh
        position={[0, y + boxH / 2, 0]}
        castShadow
        onClick={(e) => {
          e.stopPropagation();
          onSelect();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          onHover();
        }}
        onPointerOut={onOut}
      >
        <boxGeometry args={[RACK_W * 0.82, boxH, depth * 0.9]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 0.85 : bay.replenishment_required ? 0.45 : 0.12}
          roughness={0.62}
          metalness={0.08}
        />
      </mesh>

      {/* Strap detail so loads read as cartons, not plain cubes */}
      <mesh position={[0, y + boxH / 2, depth * 0.46]}>
        <planeGeometry args={[RACK_W * 0.82, boxH * 0.14]} />
        <meshBasicMaterial color="#141821" transparent opacity={0.5} />
      </mesh>
    </group>
  );
}

export function AisleObject({ aisle }: Props) {
  const allBays = useDataStore((s) => s.bays);
  const setSelected = useUIStore((s) => s.setSelected);
  const setHovered = useUIStore((s) => s.setHovered);
  const hovered = useUIStore((s) => s.hoveredObject);
  const selected = useUIStore((s) => s.selectedObject);

  const bays = useMemo(
    () => allBays.filter((b) => b.aisle_id === aisle.id),
    [allBays, aisle.id],
  );

  const isHovered = hovered?.type === 'aisle' && hovered.id === aisle.id;
  const isSelected = selected?.type === 'aisle' && selected.id === aisle.id;

  const runLength = SITE.aisle.baysPerAisle * SITE.aisle.bayDepth;
  const rackH = LEVELS * LEVEL_H;
  const identity = { type: 'aisle' as const, id: aisle.id, code: aisle.code };

  // Uprights at every bay boundary.
  const uprightZ = useMemo(
    () =>
      Array.from({ length: SITE.aisle.baysPerAisle + 1 }, (_, i) => i * SITE.aisle.bayDepth - SITE.aisle.bayDepth / 2),
    [],
  );

  return (
    <group position={[aisle.position_x, 0, aisle.position_z]}>
      {/* Painted pick lane down the middle */}
      <mesh
        position={[0, 0.03, runLength / 2 - SITE.aisle.bayDepth / 2]}
        rotation={[-Math.PI / 2, 0, 0]}
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
        <planeGeometry args={[RACK_W * 2 + 2.6, runLength]} />
        <meshStandardMaterial
          color={isSelected ? COLORS.cyan : '#4a5163'}
          emissive={isSelected ? COLORS.cyan : '#000000'}
          emissiveIntensity={isSelected ? 0.35 : 0}
          roughness={0.9}
        />
      </mesh>

      {/* Lane edge striping */}
      {[-1, 1].map((side) => (
        <mesh
          key={side}
          position={[side * (RACK_W + 1.25), 0.04, runLength / 2 - SITE.aisle.bayDepth / 2]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <planeGeometry args={[0.16, runLength]} />
          <meshBasicMaterial color={COLORS.amber} transparent opacity={0.5} />
        </mesh>
      ))}

      {/* Rack uprights, both faces */}
      {[-1, 1].map((side) =>
        uprightZ.map((z) => (
          <mesh
            key={`${side}-${z}`}
            position={[side * (RACK_W / 2 + 0.1), rackH / 2, z]}
            castShadow
          >
            <boxGeometry args={[RACK_W, rackH, UPRIGHT]} />
            <meshStandardMaterial color={MATERIAL.rackUpright} roughness={0.55} metalness={0.55} />
          </mesh>
        )),
      )}

      {/* Horizontal beams at each level */}
      {[-1, 1].map((side) =>
        Array.from({ length: LEVELS }, (_, lvl) => (
          <mesh
            key={`${side}-b${lvl}`}
            position={[
              side * (RACK_W / 2 + 0.1),
              lvl * LEVEL_H + 0.42,
              runLength / 2 - SITE.aisle.bayDepth / 2,
            ]}
          >
            <boxGeometry args={[RACK_W * 0.98, 0.12, runLength]} />
            <meshStandardMaterial color={COLORS.amber} roughness={0.6} metalness={0.35} />
          </mesh>
        )),
      )}

      {/* Palletised loads */}
      {bays.map((bay, i) => (
        <group key={bay.id} position={[0, 0, bay.position_index * SITE.aisle.bayDepth]}>
          <PalletLoad
            bay={bay}
            side={i % 2 === 0 ? -1 : 1}
            selected={selected?.type === 'bay' && selected.id === bay.id}
            onSelect={() => setSelected({ type: 'bay', id: bay.id, code: bay.code })}
            onHover={() => setHovered({ type: 'bay', id: bay.id, code: bay.code })}
            onOut={() => setHovered(null)}
          />
        </group>
      ))}

      {/* Aisle label on the floor at the head of the run */}
      <Text
        position={[0, 0.06, -SITE.aisle.bayDepth]}
        rotation={[-Math.PI / 2, 0, 0]}
        fontSize={1.5}
        color={isSelected ? COLORS.cyan : '#9aa5bd'}
        anchorX="center"
        anchorY="middle"
      >
        {aisle.code}
      </Text>

      {/* Zone banner above the run */}
      <Text
        position={[0, rackH + 1.4, runLength / 2 - SITE.aisle.bayDepth / 2]}
        rotation={[0, Math.PI / 2, 0]}
        fontSize={1.1}
        color="#7f8ba6"
        anchorX="center"
        anchorY="middle"
      >
        {aisle.zone ?? ''}
      </Text>

      {isHovered && (
        <Html position={[0, rackH + 3, runLength / 2]} center distanceFactor={42}>
          <div className="object-tooltip">
            <div className="tooltip-code">
              {aisle.code} · {aisle.zone ?? 'ZONE'}
            </div>
            <div className="tooltip-status">
              {aisle.occupied_pct.toFixed(0)}% occupied · {aisle.active_pick_tasks} picks
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}
