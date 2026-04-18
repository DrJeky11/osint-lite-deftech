<script>
  import { filters } from "../state.svelte.js";
  import { dataset } from "../generated/osint-data.js";
  import { unique } from "../lib/format.js";

  let { onFilterChange = () => {}, onProjectionChange = () => {} } = $props();

  const sourceOptions = [
    { value: "all", label: "All sources" },
    ...unique(dataset.signalEvents.map((event) => event.sourceFamily)).map((family) => ({
      value: family,
      label: family.charAt(0).toUpperCase() + family.slice(1)
    }))
  ];

  function handleProjection(event) {
    filters.projection = event.target.value;
    onProjectionChange();
  }

  function handleTimeWindow(event) {
    filters.timeWindowHours = Number(event.target.value);
    onFilterChange();
  }

  function handleSourceFamily(event) {
    filters.sourceFamily = event.target.value;
    onFilterChange();
  }

  function handleEmphasis(event) {
    filters.emphasis = event.target.value;
    onFilterChange();
  }

  function handleConfidence(event) {
    filters.confidenceFloor = Number(event.target.value) / 100;
    onFilterChange();
  }

  function handleHeatmap(event) {
    filters.heatmapEnabled = event.target.checked;
    onFilterChange();
  }
</script>

<div class="flex flex-wrap items-end gap-3 py-3 px-4 border border-line bg-panel-soft text-[0.8rem]">
  <label class="grid gap-1 text-control-label min-w-[110px]">
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Projection</span>
    <select
      value={filters.projection}
      onchange={handleProjection}
      class="appearance-none border border-line bg-panel-strong text-text font-mono text-[0.75rem] px-2 py-1.5 w-full focus:outline-1 focus:outline-blue/30 focus:outline-offset-1"
    >
      <option value="globe">Globe</option>
      <option value="mercator">Mercator</option>
    </select>
  </label>

  <label class="grid gap-1 text-control-label min-w-[110px]">
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Window</span>
    <select
      value={String(filters.timeWindowHours)}
      onchange={handleTimeWindow}
      class="appearance-none border border-line bg-panel-strong text-text font-mono text-[0.75rem] px-2 py-1.5 w-full focus:outline-1 focus:outline-blue/30 focus:outline-offset-1"
    >
      <option value="6">6h</option>
      <option value="12">12h</option>
      <option value="24">24h</option>
      <option value="36">36h</option>
    </select>
  </label>

  <label class="grid gap-1 text-control-label min-w-[110px]">
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Source</span>
    <select
      value={filters.sourceFamily}
      onchange={handleSourceFamily}
      class="appearance-none border border-line bg-panel-strong text-text font-mono text-[0.75rem] px-2 py-1.5 w-full focus:outline-1 focus:outline-blue/30 focus:outline-offset-1"
    >
      {#each sourceOptions as opt}
        <option value={opt.value}>{opt.label}</option>
      {/each}
    </select>
  </label>

  <label class="grid gap-1 text-control-label min-w-[110px]">
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Emphasis</span>
    <select
      value={filters.emphasis}
      onchange={handleEmphasis}
      class="appearance-none border border-line bg-panel-strong text-text font-mono text-[0.75rem] px-2 py-1.5 w-full focus:outline-1 focus:outline-blue/30 focus:outline-offset-1"
    >
      <option value="blend">Blended</option>
      <option value="civil">Civil</option>
      <option value="military">Military</option>
    </select>
  </label>

  <label class="flex items-center gap-2 cursor-pointer text-control-label py-1.5">
    <input
      type="checkbox"
      checked={filters.heatmapEnabled}
      onchange={handleHeatmap}
      class="w-3.5 h-3.5 accent-[var(--color-blue)] cursor-pointer"
    />
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Heatmap</span>
  </label>

  <label class="grid gap-1 text-control-label min-w-[140px]">
    <span class="font-mono text-[0.6rem] tracking-[0.12em] uppercase text-muted">Confidence &ge; {Math.round(filters.confidenceFloor * 100)}%</span>
    <input
      type="range"
      min="35"
      max="90"
      value={filters.confidenceFloor * 100}
      oninput={handleConfidence}
      class="w-full accent-amber h-1.5"
    />
  </label>
</div>
