/** A repeatable illustrative execution, using OMAR's diagram states and shapes. */
export const MACHINE_CYCLE_MS = 24000;
export type Window = readonly [number, number];
export const reactionSchedule: Record<string, readonly Window[]> = {
  plan: [
    [800, 2400],
    [12400, 13600],
  ],
  dispatch: [
    [2700, 3100],
    [13900, 14200],
  ],
  gather: [
    [8400, 8600],
    [17900, 17950],
  ],
  research: [
    [4000, 6000],
    [14500, 16000],
  ],
  build: [
    [4000, 7000],
    [14500, 17000],
  ],
  review: [
    [8800, 10500],
    [18000, 19200],
  ],
  publish: [[19600, 21000]],
};
export function reactionState(
  id: string,
  time: number,
): "idle" | "running" | "completed" {
  const windows = reactionSchedule[id] ?? [];
  if (windows.some(([start, end]) => time >= start && time < end))
    return "running";
  return windows.some(([, end]) => time >= end) ? "completed" : "idle";
}
export function activeWindow(
  windows: readonly Window[],
  time: number,
): number | null {
  const window = windows.find(([start, end]) => time >= start && time < end);
  return window ? (time - window[0]) / (window[1] - window[0]) : null;
}
