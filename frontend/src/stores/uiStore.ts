/* ── UI Store — selected object, camera, panels, command bar ── */
import { create } from 'zustand';
import type { AIQueryResponse, CameraView, SelectedObject } from '@/types/types';
import { api } from '@/services/api';

interface UIState {
  // Selection
  selectedObject: SelectedObject | null;
  hoveredObject: SelectedObject | null;
  setSelected: (obj: SelectedObject | null) => void;
  setHovered: (obj: SelectedObject | null) => void;

  // Camera
  cameraView: CameraView;
  cameraTarget: [number, number, number] | null;
  setCameraView: (view: CameraView, target?: [number, number, number]) => void;

  // Sidebar
  activePage: string;
  setActivePage: (page: string) => void;

  // Command bar
  commandBarOpen: boolean;
  commandBarQuery: string;
  commandBarResponse: AIQueryResponse | null;
  commandBarLoading: boolean;
  setCommandBarOpen: (open: boolean) => void;
  setCommandBarQuery: (q: string) => void;
  submitQuery: (q: string) => Promise<void>;

  // Loading
  dataLoaded: boolean;
  setDataLoaded: (v: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedObject: null,
  hoveredObject: null,
  setSelected: (obj) => set({ selectedObject: obj }),
  setHovered: (obj) => set({ hoveredObject: obj }),

  cameraView: 'overview',
  cameraTarget: null,
  setCameraView: (view, target) => set({ cameraView: view, cameraTarget: target ?? null }),

  activePage: 'digital-twin',
  setActivePage: (page) => set({ activePage: page }),

  commandBarOpen: false,
  commandBarQuery: '',
  commandBarResponse: null,
  commandBarLoading: false,
  setCommandBarOpen: (open) => set({ commandBarOpen: open }),
  setCommandBarQuery: (q) => set({ commandBarQuery: q }),
  submitQuery: async (q) => {
    set({ commandBarLoading: true });
    try {
      const res = await api.aiQuery(q);
      set({ commandBarResponse: res, commandBarLoading: false });
    } catch {
      set({
        commandBarResponse: { query: q, response: 'Failed to reach ChainPilot AI.', suggestions: [] },
        commandBarLoading: false,
      });
    }
  },

  dataLoaded: false,
  setDataLoaded: (v) => set({ dataLoaded: v }),
}));
