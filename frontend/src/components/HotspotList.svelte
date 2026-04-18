<script>
  import { selection } from "../state.svelte.js";
  import { formatDelta, selectedLabel } from "../lib/format.js";

  let { visibleScores = [], onSelect = () => {} } = $props();

  /** Interpolate the same heat color ramp used on the map: #49d4ba → #ffb25f → #ff7557 */
  function heatColor(heat) {
    const stops = [
      [0,   [0x49, 0xd4, 0xba]],
      [50,  [0xff, 0xb2, 0x5f]],
      [100, [0xff, 0x75, 0x57]],
    ];
    const h = Math.max(0, Math.min(100, heat));
    let lo = stops[0], hi = stops[stops.length - 1];
    for (let i = 0; i < stops.length - 1; i++) {
      if (h >= stops[i][0] && h <= stops[i + 1][0]) {
        lo = stops[i];
        hi = stops[i + 1];
        break;
      }
    }
    const t = hi[0] === lo[0] ? 0 : (h - lo[0]) / (hi[0] - lo[0]);
    const r = Math.round(lo[1][0] + t * (hi[1][0] - lo[1][0]));
    const g = Math.round(lo[1][1] + t * (hi[1][1] - lo[1][1]));
    const b = Math.round(lo[1][2] + t * (hi[1][2] - lo[1][2]));
    return `rgb(${r},${g},${b})`;
  }
</script>

<div class="grid grid-cols-3 gap-px bg-line max-[1100px]:grid-cols-2 max-[560px]:grid-cols-1">
  {#if visibleScores.length === 0}
    <p class="m-0 p-4 bg-bg text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase col-span-full">No theaters match the active filters</p>
  {:else}
    {#each visibleScores.slice(0, 6) as score, index}
      <button
        type="button"
        class="grid gap-1 text-left p-4 bg-bg transition-all duration-150 ease-out hover:bg-[rgba(255,178,95,0.04)]"
        class:active-chip={score.id === selection.locationId}
        onclick={() => onSelect(score.id)}
      >
        <span class="font-mono uppercase tracking-[0.14em] text-[0.6rem] text-muted">{String(index + 1).padStart(2, "0")}</span>
        <span class="text-[0.95rem] font-semibold leading-tight">{score.name}</span>
        <span class="font-mono text-[0.75rem] tabular-nums">
          <span class="text-chip-delta">{formatDelta(score.delta)} delta</span>
          <span class="text-chip-delta"> &middot; </span>
          <span style="color: {heatColor(score.heat)}">{score.heat.toFixed(0)} heat</span>
        </span>
        <span class="font-mono uppercase tracking-[0.1em] text-[0.6rem] text-muted">{selectedLabel(score)}</span>
      </button>
    {/each}
  {/if}
</div>

<style>
  .active-chip {
    background: rgba(255, 178, 95, 0.06);
    box-shadow: inset 3px 0 0 rgba(255, 178, 95, 0.6);
  }
</style>
