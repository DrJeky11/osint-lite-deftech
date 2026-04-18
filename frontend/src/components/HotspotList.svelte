<script>
  import { selection } from "../state.svelte.js";
  import { formatDelta, selectedLabel } from "../lib/format.js";

  let { visibleScores = [], onSelect = () => {} } = $props();
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
        <span class="font-mono text-[0.75rem] text-chip-delta tabular-nums">{formatDelta(score.delta)} delta &middot; {score.heat.toFixed(0)} heat</span>
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
