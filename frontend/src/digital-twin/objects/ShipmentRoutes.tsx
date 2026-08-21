/* ── ShipmentRoutes — inbound/outbound arcs into the site, coloured by risk ── */
import { useMemo } from 'react';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { useDataStore } from '@/stores/dataStore';
import { COLORS, SITE, severityColor } from '@/constants';

const ARRIVAL = new THREE.Vector3(SITE.apron.x - 6, 0.5, 0);

/** Fans routes out around the approach so they do not overlap. */
function endpointFor(index: number, total: number, inbound: boolean): THREE.Vector3 {
  const spread = Math.PI * 0.55;
  const angle = total > 1 ? -spread / 2 + (index / (total - 1)) * spread : 0;
  const radius = 95;
  const dir = inbound ? -1 : 1;
  return new THREE.Vector3(
    ARRIVAL.x + dir * radius * Math.cos(angle),
    0.5,
    ARRIVAL.z + radius * Math.sin(angle) * (inbound ? 1 : -1),
  );
}

export function ShipmentRoutes() {
  const shipments = useDataStore((s) => s.shipments);

  // Only routes still in play are worth drawing.
  const active = useMemo(
    () =>
      shipments.filter(
        (s) => s.status === 'IN_TRANSIT' || s.status === 'SCHEDULED' || s.status === 'DELAYED',
      ),
    [shipments],
  );

  const routes = useMemo(() => {
    const inbound = active.filter((s) => s.direction === 'INBOUND');
    const outbound = active.filter((s) => s.direction === 'OUTBOUND');

    const build = (list: typeof active, isInbound: boolean) =>
      list.map((s, i) => {
        const far = endpointFor(i, list.length, isInbound);
        const mid = new THREE.Vector3()
          .addVectors(ARRIVAL, far)
          .multiplyScalar(0.5)
          .setY(14 + (i % 4) * 3);

        const curve = new THREE.QuadraticBezierCurve3(
          isInbound ? far : ARRIVAL,
          mid,
          isInbound ? ARRIVAL : far,
        );

        return {
          id: s.id,
          points: curve.getPoints(36).map((p) => [p.x, p.y, p.z] as [number, number, number]),
          color: s.status === 'DELAYED' ? severityColor('CRITICAL') : severityColor(s.risk),
          delayed: s.status === 'DELAYED',
        };
      });

    return [...build(inbound, true), ...build(outbound, false)];
  }, [active]);

  return (
    <group>
      {routes.map((r) => (
        <Line
          key={r.id}
          points={r.points}
          color={r.color}
          lineWidth={r.delayed ? 1.8 : 1}
          transparent
          opacity={r.delayed ? 0.85 : 0.35}
          dashed={!r.delayed}
          dashSize={2}
          gapSize={1.6}
        />
      ))}

      {/* Convergence marker at the site entry */}
      <mesh position={[ARRIVAL.x, 0.4, ARRIVAL.z]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[1.8, 2.2, 32]} />
        <meshBasicMaterial color={COLORS.cyan} transparent opacity={0.5} />
      </mesh>
    </group>
  );
}
