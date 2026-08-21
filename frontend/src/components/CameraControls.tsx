/* ── CameraControls — camera view presets (bottom right) ── */
import { useUIStore } from '@/stores/uiStore';
import type { CameraView } from '@/types/types';

const VIEWS: Array<{ id: CameraView; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'yard', label: 'Yard' },
  { id: 'warehouse', label: 'Warehouse' },
];

export function CameraControls() {
  const cameraView = useUIStore((s) => s.cameraView);
  const setCameraView = useUIStore((s) => s.setCameraView);

  return (
    <div className="camera-controls">
      {VIEWS.map((v) => (
        <button
          key={v.id}
          className={`camera-btn ${cameraView === v.id ? 'active' : ''}`}
          // Clearing the target releases any object-follow lock.
          onClick={() => setCameraView(v.id)}
        >
          {v.label}
        </button>
      ))}
    </div>
  );
}
