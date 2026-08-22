/* ── Shared hooks ── */
import { SCENE, type SceneTheme } from '@/constants';
import { useUIStore } from '@/stores/uiStore';

/** Structural scene colours for the active theme. */
export function useSceneColors(): SceneTheme {
  const theme = useUIStore((s) => s.theme);
  return SCENE[theme];
}
