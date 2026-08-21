/* ── UI Store — selection, camera, panels, agent console ── */
import { create } from 'zustand';
import type { AIQueryResponse, CameraView, SelectedObject } from '@/types/types';
import { api } from '@/services/api';
import { useDataStore } from '@/stores/dataStore';

type Panel = 'agent' | 'tower' | 'detail';

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

  // Mobile: which sheet is on top
  activePanel: Panel;
  setActivePanel: (p: Panel) => void;

  // Command bar + agent run
  commandBarQuery: string;
  commandBarLoading: boolean;
  agentRun: AIQueryResponse | null;
  decidingActionId: number | null;
  actionError: string | null;
  setCommandBarQuery: (q: string) => void;
  submitQuery: (q: string) => Promise<void>;
  closeAgentRun: () => void;
  decideAction: (id: number, decision: 'approve' | 'reject') => Promise<void>;

  // Loading
  dataLoaded: boolean;
  setDataLoaded: (v: boolean) => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  selectedObject: null,
  hoveredObject: null,
  setSelected: (obj) =>
    set(obj ? { selectedObject: obj, activePanel: 'detail' } : { selectedObject: obj }),
  setHovered: (obj) => set({ hoveredObject: obj }),

  cameraView: 'overview',
  cameraTarget: null,
  setCameraView: (view, target) => set({ cameraView: view, cameraTarget: target ?? null }),

  activePage: 'digital-twin',
  setActivePage: (page) => set({ activePage: page }),

  activePanel: 'tower',
  setActivePanel: (p) => set({ activePanel: p }),

  commandBarQuery: '',
  commandBarLoading: false,
  agentRun: null,
  decidingActionId: null,

  setCommandBarQuery: (q) => set({ commandBarQuery: q }),

  submitQuery: async (q) => {
    set({ commandBarLoading: true, commandBarQuery: q, activePanel: 'agent' });
    try {
      const res = await api.aiQuery(q);
      set({ agentRun: res, commandBarLoading: false });
    } catch (e) {
      set({
        agentRun: {
          query: q,
          response:
            `Could not reach the agent service (${(e as Error).message}). ` +
            'Check that the backend is running on port 8000.',
          suggestions: [],
          agents: [],
          actions: [],
        },
        commandBarLoading: false,
      });
    }
  },

  closeAgentRun: () => set({ agentRun: null, activePanel: 'tower' }),

  actionError: null,

  decideAction: async (id, decision) => {
    set({ decidingActionId: id, actionError: null });
    try {
      const res =
        decision === 'approve' ? await api.approveAction(id) : await api.rejectAction(id);

      // Reflect the decision in the open run without refetching everything.
      const run = get().agentRun;
      if (run && res.action) {
        set({
          agentRun: {
            ...run,
            actions: run.actions.map((a) => (a.id === id ? res.action! : a)),
          },
        });
      }

      // An executed action mutates operational state — pull the twin back
      // in sync so the change is visible immediately.
      if (decision === 'approve' && res.ok) {
        await useDataStore.getState().fetchAll();
      }
      if (!res.ok) set({ actionError: res.message });
    } catch (e) {
      // Surface the failure — silently swallowing it leaves the operator
      // thinking an action was applied when it was not.
      set({ actionError: (e as Error).message });
    } finally {
      set({ decidingActionId: null });
    }
  },

  dataLoaded: false,
  setDataLoaded: (v) => set({ dataLoaded: v }),
}));
