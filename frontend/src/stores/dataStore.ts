/* ── Data store — all domain entities fetched from backend ── */
import { create } from 'zustand';
import { api } from '@/services/api';
import type {
  Aisle,
  Bay,
  CustomerOrder,
  Dock,
  Forklift,
  HealthSummary,
  InventoryItem,
  OperationalEvent,
  OperationalException,
  Pallet,
  ParkingSlot,
  Shipment,
  Truck,
  Warehouse,
} from '@/types/types';

interface DataState {
  warehouses: Warehouse[];
  aisles: Aisle[];
  bays: Bay[];
  docks: Dock[];
  parkingSlots: ParkingSlot[];
  trucks: Truck[];
  shipments: Shipment[];
  pallets: Pallet[];
  inventory: InventoryItem[];
  forklifts: Forklift[];
  orders: CustomerOrder[];
  events: OperationalEvent[];
  exceptions: OperationalException[];
  health: HealthSummary | null;

  loading: boolean;
  error: string | null;

  fetchAll: () => Promise<void>;
}

export const useDataStore = create<DataState>((set) => ({
  warehouses: [],
  aisles: [],
  bays: [],
  docks: [],
  parkingSlots: [],
  trucks: [],
  shipments: [],
  pallets: [],
  inventory: [],
  forklifts: [],
  orders: [],
  events: [],
  exceptions: [],
  health: null,

  loading: false,
  error: null,

  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      const [
        warehouses, aisles, bays, docks, parkingSlots,
        trucks, shipments, pallets, inventory, forklifts,
        orders, events, exceptions, health,
      ] = await Promise.all([
        api.warehouses(),
        api.aisles(),
        api.bays(),
        api.docks(),
        api.parkingSlots(),
        api.trucks(),
        api.shipments(),
        api.pallets(),
        api.inventory(),
        api.forklifts(),
        api.orders(),
        api.events(),
        api.exceptions(),
        api.health(),
      ]);
      set({
        warehouses, aisles, bays, docks, parkingSlots,
        trucks, shipments, pallets, inventory, forklifts,
        orders, events, exceptions, health,
        loading: false,
      });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },
}));
