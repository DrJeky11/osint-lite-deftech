<script>
  import { getVisibleScores, getFilteredSignalEvents } from "../state.svelte.js";
  import { formatDelta } from "../lib/format.js";
  import TrendPill from "./TrendPill.svelte";
  import Sparkline from "./Sparkline.svelte";

  let { visibleScores = [], filteredEvents = [], onHotspotSelect = () => {} } = $props();

  /* ── Region definitions ── */
  const PRESETS = [
    { name: "Middle East & North Africa", countries: ["Lebanon","Syria","Iraq","Iran","Yemen","Libya","Egypt","Tunisia","Jordan","Israel","Palestine","Saudi Arabia","Bahrain","Qatar","UAE","Oman","Kuwait","Algeria","Morocco"] },
    { name: "Sub-Saharan Africa", countries: ["Sudan","South Sudan","Ethiopia","Somalia","Nigeria","DRC","Congo","Mali","Burkina Faso","Niger","Chad","Cameroon","Kenya","Uganda","Tanzania","Mozambique","Zimbabwe","Central African Republic","Myanmar"] },
    { name: "Indo-Pacific", countries: ["China","Taiwan","Philippines","Vietnam","Myanmar","Thailand","Indonesia","Malaysia","North Korea","South Korea","Japan","India","Australia","Papua New Guinea","Laos","Cambodia"] },
    { name: "Europe & Eurasia", countries: ["Ukraine","Russia","Belarus","Georgia","Moldova","Armenia","Azerbaijan","Serbia","Kosovo","Bosnia","Turkey","Poland","Romania","Baltic","Latvia","Lithuania","Estonia","Finland"] },
    { name: "South & Central Asia", countries: ["Pakistan","Afghanistan","India","Bangladesh","Sri Lanka","Nepal","Kazakhstan","Uzbekistan","Tajikistan","Kyrgyzstan","Turkmenistan"] },
    { name: "Americas", countries: ["Venezuela","Colombia","Mexico","Haiti","Cuba","Nicaragua","Honduras","Guatemala","El Salvador","Ecuador","Peru","Brazil","Bolivia","Chile","Argentina"] },
  ];

  /* ── Persisted user regions ── */
  const STORAGE_KEY = "sa-user-regions";

  function loadRegions() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch { return []; }
  }

  function saveRegions(regions) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(regions));
  }

  let userRegions = $state(loadRegions());

  /* ── Add region modal state ── */
  let showAddPanel = $state(false);
  let customName = $state("");
  let customCountries = $state("");
  let selectedPreset = $state(null);

  function addPreset(preset) {
    const already = userRegions.some(r => r.name === preset.name);
    if (already) return;
    userRegions = [...userRegions, { name: preset.name, countries: [...preset.countries] }];
    saveRegions(userRegions);
  }

  function addCustomRegion() {
    const name = customName.trim();
    const countries = customCountries.split(",").map(c => c.trim()).filter(Boolean);
    if (!name || !countries.length) return;
    userRegions = [...userRegions, { name, countries }];
    saveRegions(userRegions);
    customName = "";
    customCountries = "";
    showAddPanel = false;
  }

  function removeRegion(index) {
    userRegions = userRegions.filter((_, i) => i !== index);
    saveRegions(userRegions);
  }

  /* ── Compute regional aggregates ── */
  function regionStats(region) {
    // Match scores whose name contains any of the region's country names
    const matchingScores = visibleScores.filter(s =>
      region.countries.some(c => s.name.toLowerCase().includes(c.toLowerCase()))
    );
    const matchingEvents = filteredEvents.filter(e =>
      region.countries.some(c =>
        (e.geo?.country ?? e.geo?.name ?? "").toLowerCase().includes(c.toLowerCase())
      )
    );

    const totalHeat = matchingScores.reduce((sum, s) => sum + s.heat, 0);
    const avgHeat = matchingScores.length ? totalHeat / matchingScores.length : 0;
    const maxDelta = matchingScores.length
      ? matchingScores.reduce((best, s) => Math.abs(s.delta) > Math.abs(best.delta) ? s : best, matchingScores[0])
      : null;
    const topHotspot = matchingScores[0] ?? null; // already sorted by heat desc

    // Aggregate trend: majority vote — suppress when data is too thin
    let dominantTrend = "steady";
    if (matchingScores.length && avgHeat >= 1) {
      const trendCounts = { warming: 0, cooling: 0, steady: 0 };
      matchingScores.forEach(s => trendCounts[s.trend]++);
      dominantTrend = Object.entries(trendCounts).sort((a,b) => b[1] - a[1])[0]?.[0] ?? "steady";
    }

    // Build aggregate history from matching scores
    const aggHistory = matchingScores.length
      ? matchingScores[0].history.map((_, i) =>
          Number((matchingScores.reduce((sum, s) => sum + (s.history[i] ?? 0), 0) / matchingScores.length).toFixed(2))
        )
      : [];

    return {
      theaters: matchingScores.length,
      signals: matchingEvents.length,
      avgHeat: Number(avgHeat.toFixed(1)),
      topHotspot,
      dominantTrend,
      history: aggHistory,
    };
  }

  /* ── Heat color ramp ── */
  function heatColor(heat) {
    const stops = [
      [0,   [0x49, 0xd4, 0xba]],
      [50,  [0xff, 0xb2, 0x5f]],
      [100, [0xff, 0x75, 0x57]],
    ];
    const h = Math.max(0, Math.min(100, heat));
    let lo = stops[0], hi = stops[stops.length - 1];
    for (let i = 0; i < stops.length - 1; i++) {
      if (h >= stops[i][0] && h <= stops[i + 1][0]) { lo = stops[i]; hi = stops[i + 1]; break; }
    }
    const t = hi[0] === lo[0] ? 0 : (h - lo[0]) / (hi[0] - lo[0]);
    const r = Math.round(lo[1][0] + t * (hi[1][0] - lo[1][0]));
    const g = Math.round(lo[1][1] + t * (hi[1][1] - lo[1][1]));
    const b = Math.round(lo[1][2] + t * (hi[1][2] - lo[1][2]));
    return `rgb(${r},${g},${b})`;
  }

  /** Check which presets are already added */
  const addedPresets = $derived(new Set(userRegions.map(r => r.name)));
</script>

<!-- Regional Summary Cards -->
<div class="mt-6">
  <div class="flex items-center gap-3 mb-3">
    <span class="section-flag">Regional Watch</span>
    <hr class="rule-thin flex-1" />
    <button
      type="button"
      class="add-region-btn"
      onclick={() => showAddPanel = !showAddPanel}
    >
      {#if showAddPanel}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        Close
      {:else}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        Add Region
      {/if}
    </button>
  </div>

  <!-- ── Add Region Panel ── -->
  {#if showAddPanel}
    <div class="add-panel glass-panel p-4 mb-4">
      <p class="m-0 mb-3 font-mono text-[0.65rem] tracking-[0.14em] uppercase text-muted">Quick-add preset regions</p>
      <div class="flex flex-wrap gap-2 mb-4">
        {#each PRESETS as preset}
          <button
            type="button"
            class="preset-chip"
            class:preset-added={addedPresets.has(preset.name)}
            disabled={addedPresets.has(preset.name)}
            onclick={() => addPreset(preset)}
          >
            {#if addedPresets.has(preset.name)}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M20 6L9 17l-5-5"/></svg>
            {:else}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            {/if}
            {preset.name}
          </button>
        {/each}
      </div>

      <hr class="rule-thin mb-3" />
      <p class="m-0 mb-2 font-mono text-[0.65rem] tracking-[0.14em] uppercase text-muted">Or define a custom region</p>
      <div class="grid gap-2">
        <input
          type="text"
          bind:value={customName}
          placeholder="Region name (e.g. Horn of Africa)"
          class="custom-input"
        />
        <input
          type="text"
          bind:value={customCountries}
          placeholder="Countries, comma-separated (e.g. Somalia, Ethiopia, Eritrea)"
          class="custom-input"
        />
        <button
          type="button"
          class="add-custom-btn"
          disabled={!customName.trim() || !customCountries.trim()}
          onclick={addCustomRegion}
        >
          Add Custom Region
        </button>
      </div>
    </div>
  {/if}

  <!-- ── Region Cards Grid ── -->
  {#if userRegions.length === 0}
    <div class="empty-state">
      <p class="m-0 text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">
        No regions tracked &mdash; click "Add Region" to start monitoring areas of interest
      </p>
    </div>
  {:else}
    <div class="grid grid-cols-2 gap-px bg-line max-[1100px]:grid-cols-1">
      {#each userRegions as region, index}
        {@const stats = regionStats(region)}
        <div class="region-card bg-bg p-4">
          <!-- Card Header -->
          <div class="flex items-start justify-between gap-2 mb-3">
            <div class="flex-1 min-w-0">
              <h3 class="m-0 text-[0.92rem] font-semibold leading-tight truncate">{region.name}</h3>
              <span class="font-mono text-[0.58rem] tracking-[0.1em] text-muted uppercase">
                {region.countries.length} countries monitored
              </span>
            </div>
            <div class="flex items-center gap-2">
              <TrendPill trend={stats.dominantTrend} />
              <button
                type="button"
                class="remove-btn"
                onclick={() => removeRegion(index)}
                title="Remove region"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- Metrics Row -->
          <div class="grid grid-cols-3 gap-3 mb-3">
            <div class="metric-cell">
              <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">Theaters</span>
              <strong class="text-lg leading-none tabular-nums">{stats.theaters}</strong>
            </div>
            <div class="metric-cell">
              <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">Signals</span>
              <strong class="text-lg leading-none tabular-nums">{stats.signals}</strong>
            </div>
            <div class="metric-cell">
              <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">Avg Heat</span>
              <strong class="text-lg leading-none tabular-nums" style="color: {heatColor(stats.avgHeat)}">{stats.avgHeat}</strong>
            </div>
          </div>

          <!-- Sparkline -->
          {#if stats.history.length}
            <div class="mb-3">
              <Sparkline history={stats.history} />
            </div>
          {/if}

          <!-- Top Hotspot -->
          {#if stats.topHotspot}
            <button
              type="button"
              class="top-hotspot"
              onclick={() => onHotspotSelect(stats.topHotspot.id)}
            >
              <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">Top hotspot</span>
              <span class="text-[0.82rem] font-medium">{stats.topHotspot.name}</span>
              <span class="font-mono text-[0.72rem] tabular-nums">
                <span style="color: {heatColor(stats.topHotspot.heat)}">{stats.topHotspot.heat.toFixed(0)} heat</span>
                <span class="text-muted"> &middot; </span>
                <span class="text-chip-delta">{formatDelta(stats.topHotspot.delta)} delta</span>
              </span>
            </button>
          {:else}
            <p class="m-0 font-mono text-[0.65rem] text-muted tracking-[0.06em]">No active signals in this region</p>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .add-region-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: rgba(120, 214, 255, 0.06);
    border: 1px solid rgba(120, 214, 255, 0.18);
    color: var(--color-blue);
    font-family: var(--font-mono);
    font-size: 0.6rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .add-region-btn:hover {
    background: rgba(120, 214, 255, 0.12);
    border-color: rgba(120, 214, 255, 0.32);
  }

  .preset-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    background: rgba(120, 214, 255, 0.04);
    border: 1px solid rgba(120, 214, 255, 0.14);
    color: var(--color-body-light);
    font-family: var(--font-mono);
    font-size: 0.62rem;
    letter-spacing: 0.08em;
    cursor: pointer;
    transition: all 0.15s;
  }
  .preset-chip:hover:not(:disabled) {
    background: rgba(120, 214, 255, 0.1);
    border-color: rgba(120, 214, 255, 0.3);
  }
  .preset-added {
    background: rgba(73, 212, 186, 0.08);
    border-color: rgba(73, 212, 186, 0.24);
    color: var(--color-civil);
    cursor: default;
  }

  .custom-input {
    width: 100%;
    padding: 8px 12px;
    background: rgba(6, 12, 22, 0.6);
    border: 1px solid var(--color-line);
    color: var(--color-text);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    outline: none;
    transition: border-color 0.15s;
  }
  .custom-input::placeholder {
    color: var(--color-muted);
    opacity: 0.6;
  }
  .custom-input:focus {
    border-color: rgba(120, 214, 255, 0.4);
  }

  .add-custom-btn {
    padding: 8px 16px;
    background: rgba(120, 214, 255, 0.08);
    border: 1px solid rgba(120, 214, 255, 0.2);
    color: var(--color-blue);
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
  }
  .add-custom-btn:hover:not(:disabled) {
    background: rgba(120, 214, 255, 0.14);
  }
  .add-custom-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .empty-state {
    padding: 24px;
    border: 1px dashed var(--color-line);
    text-align: center;
  }

  .region-card {
    transition: background 0.15s;
  }
  .region-card:hover {
    background: rgba(255, 178, 95, 0.02);
  }

  .metric-cell {
    display: grid;
    gap: 4px;
  }

  .remove-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: none;
    border: 1px solid transparent;
    color: var(--color-muted);
    cursor: pointer;
    opacity: 0.4;
    transition: all 0.15s;
  }
  .remove-btn:hover {
    opacity: 1;
    color: var(--color-military);
    border-color: rgba(255, 117, 87, 0.3);
  }

  .top-hotspot {
    display: grid;
    gap: 2px;
    width: 100%;
    text-align: left;
    padding: 8px 10px;
    background: rgba(255, 178, 95, 0.03);
    border: 1px solid rgba(255, 178, 95, 0.1);
    cursor: pointer;
    transition: all 0.15s;
  }
  .top-hotspot:hover {
    background: rgba(255, 178, 95, 0.07);
    border-color: rgba(255, 178, 95, 0.22);
  }
</style>
