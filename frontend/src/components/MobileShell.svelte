<script>
  import { filters, selection, getSelectedScore, dataset } from "../state.svelte.js";
  import { formatDelta, selectedLabel, unique } from "../lib/format.js";
  import MapStage from './MapStage.svelte';
  import MetricsGrid from './MetricsGrid.svelte';
  import ControlDock from './ControlDock.svelte';
  import HotspotList from './HotspotList.svelte';
  import Inspector from './Inspector.svelte';
  import RegionalSummaryCards from './RegionalSummaryCards.svelte';
  import TrendPill from './TrendPill.svelte';
  import MobileBottomSheet from './MobileBottomSheet.svelte';

  let activeTab = $state('home');
  let filtersOpen = $state(false);
  let sheetOpen = $state(false);
  let sheetExpanded = $state(false);

  // Own data state — populated by our MapStage instance
  let mapStage;
  let visibleScores = $state([]);
  let filteredEvents = $state([]);
  const selectedScore = $derived(getSelectedScore(visibleScores));
  const sourceCount = $derived(
    unique(filteredEvents.map((e) => e.sourceName ?? e.sourceFamily ?? e.source)).length
  );
  const topHotspots = $derived(visibleScores.slice(0, 3));

  // Masthead data
  const now = new Date(dataset.generatedAt);
  const timeStr = now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
  const dateStr = now.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });

  function handleDataUpdate(scores, events) {
    visibleScores = scores;
    filteredEvents = events;
  }

  function handleFilterChange() {
    mapStage?.updateMapData();
  }

  function handleProjectionChange() {
    mapStage?.applyProjection();
  }

  function handleOverlayToggle(id, visible) {
    mapStage?.handleOverlayToggle(id, visible);
  }

  // Show hotspot sheet when selection changes — plain let to avoid double-firing
  let lastSelectedId = null;
  $effect(() => {
    const id = selectedScore?.id ?? null;
    if (id && id !== lastSelectedId) {
      sheetOpen = true;
      sheetExpanded = false;
    }
    if (!id) {
      sheetOpen = false;
    }
    lastSelectedId = id;
  });

  function handleSelect(scoreId) {
    mapStage?.selectHotspot(scoreId);
  }

  function closeSheet() {
    sheetOpen = false;
    sheetExpanded = false;
    selection.locationId = null;
  }
</script>

<div class="fixed inset-0 flex flex-col bg-[#0a0e14] text-[#c9d1d9]">
  <!-- Content area -->
  <div class="flex-1 overflow-hidden relative">
    <!-- Home Tab -->
    <div
      class="absolute inset-0 overflow-y-auto"
      class:invisible={activeTab !== 'home'}
      class:pointer-events-none={activeTab !== 'home'}
    >
      <!-- Compact masthead -->
      <div class="px-4 pt-4 pb-3 text-center border-b border-[#1e2a3a]">
        <div class="flex items-center justify-center gap-2 mb-1">
          <span
            class="w-1.5 h-1.5 rounded-full bg-[#49d4ba] shrink-0"
            style="box-shadow: 0 0 8px rgba(73,212,186,0.5);"
          ></span>
          <span class="font-mono text-[0.58rem] tracking-[0.14em] uppercase text-[#5a6a7a]">Live {timeStr} UTC</span>
        </div>
        <h1 class="m-0 text-2xl tracking-[0.1em] uppercase font-light text-[#e6edf3]">Signal Atlas</h1>
        <p class="m-0 mt-0.5 font-mono text-[0.58rem] tracking-[0.08em] uppercase text-[#5a6a7a]">{dateStr}</p>
      </div>

      <!-- Metrics ribbon -->
      <div class="border-b border-[#1e2a3a]">
        <MetricsGrid
          hotspots={visibleScores.length}
          signals={filteredEvents.length}
          sources={sourceCount}
          window="{filters.timeWindowHours}h"
        />
      </div>

      <!-- Top Threats -->
      <div class="px-4 py-3">
        <div class="flex items-center gap-3 mb-3">
          <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-[#78d6ff]">Top Threats</span>
          <hr class="flex-1 border-[#1e2a3a]" />
          <button
            type="button"
            class="font-mono text-[0.55rem] tracking-[0.1em] uppercase text-[#5a6a7a] bg-transparent border-none"
            onclick={() => activeTab = 'list'}
          >View All &rarr;</button>
        </div>

        {#each topHotspots as score, i}
          <button
            type="button"
            class="w-full text-left mb-2 p-3 bg-[#0d1117] border border-[#1e2a3a] rounded-lg transition-colors active:bg-[#141c26]"
            onclick={() => { handleSelect(score.id); activeTab = 'map'; }}
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-baseline gap-2 min-w-0">
                <span class="font-mono text-[0.6rem] text-[#5a6a7a] tabular-nums shrink-0">{i + 1}.</span>
                <span class="text-[0.88rem] font-semibold text-[#e6edf3] truncate">{score.name}</span>
              </div>
              <TrendPill trend={score.trend} />
            </div>
            <div class="flex items-center gap-4 mt-2 font-mono text-[0.65rem] tabular-nums">
              <span>
                <span class="text-[#5a6a7a] tracking-[0.08em] uppercase">Heat </span>
                <span class="text-[#e6edf3]">{score.heat.toFixed(0)}</span>
              </span>
              <span>
                <span class="text-[#5a6a7a] tracking-[0.08em] uppercase">Delta </span>
                <span class="text-[#e6edf3]">{formatDelta(score.delta)}</span>
              </span>
              <span>
                <span class="text-[#5a6a7a] tracking-[0.08em] uppercase">Conf </span>
                <span class="text-[#e6edf3]">{Math.round(score.confidence * 100)}%</span>
              </span>
            </div>
          </button>
        {/each}
      </div>

      <!-- Regional Summary -->
      <div class="px-4 pb-6">
        <RegionalSummaryCards {visibleScores} {filteredEvents} onHotspotSelect={(id) => { handleSelect(id); activeTab = 'map'; }} />
      </div>

      <!-- Footer -->
      <div class="px-4 pb-6 text-center">
        <hr class="border-[#1e2a3a] mb-2" />
        <p class="m-0 font-mono text-[0.5rem] tracking-[0.16em] uppercase text-[#3a4a5a]">
          Signal Atlas &middot; All data from public sources
        </p>
      </div>
    </div>

    <!-- Map Tab (always mounted for WebGL context) -->
    <div
      class="absolute inset-0"
      class:invisible={activeTab !== 'map'}
      class:pointer-events-none={activeTab !== 'map'}
    >
      <div class="absolute inset-0">
        <MapStage bind:this={mapStage} onDataUpdate={handleDataUpdate} fullBleed={true} />
      </div>

      <!-- Floating filter button (top-right) -->
      <button
        type="button"
        class="absolute z-10 top-3 right-3 flex items-center gap-1.5 px-3 py-2 bg-[#0d1117]/90 border border-[#1e2a3a] rounded-lg text-[#78d6ff] text-xs font-mono uppercase tracking-wider backdrop-blur-sm"
        onclick={() => { filtersOpen = !filtersOpen; }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 3v1m0 16v1m-9-9h1m16 0h1m-2.636-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.314 11.314l.707.707"/>
          <circle cx="12" cy="12" r="4"/>
        </svg>
        Filters
      </button>

      <!-- Inline filter panel (slides down from top) -->
      {#if filtersOpen}
        <div
          class="absolute z-10 top-14 right-3 left-3 bg-[#0d1117]/95 border border-[#1e2a3a] rounded-lg backdrop-blur-sm overflow-hidden"
          style="animation: slideDown 0.2s ease-out;"
        >
          <div class="p-3">
            <div class="flex items-center gap-3 mb-2">
              <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-[#78d6ff]">Filters</span>
              <hr class="flex-1 border-[#1e2a3a]" />
              <button
                type="button"
                class="text-[#5a6a7a] hover:text-[#78d6ff] transition-colors"
                onclick={() => filtersOpen = false}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <ControlDock onFilterChange={handleFilterChange} onProjectionChange={handleProjectionChange} />
          </div>
        </div>
      {/if}
    </div>

    <!-- List Tab -->
    <div
      class="absolute inset-0 overflow-y-auto"
      class:invisible={activeTab !== 'list'}
      class:pointer-events-none={activeTab !== 'list'}
    >
      <!-- Metrics -->
      <div class="border-b border-[#1e2a3a] mb-4">
        <MetricsGrid
          hotspots={visibleScores.length}
          signals={filteredEvents.length}
          sources={sourceCount}
          window="{filters.timeWindowHours}h"
        />
      </div>

      <!-- Hotspot list -->
      <div>
        <div class="flex items-center gap-3 px-4 py-3">
          <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-[#78d6ff]">Priority Theaters</span>
          <hr class="flex-1 border-[#1e2a3a]" />
        </div>
        <HotspotList {visibleScores} onSelect={handleSelect} />
      </div>
    </div>

  </div>

  <!-- Bottom sheet for Inspector (outside overflow-hidden content area for correct fixed positioning) -->
  <MobileBottomSheet
    open={sheetOpen && !!selectedScore}
    bind:expanded={sheetExpanded}
    onClose={closeSheet}
  >
    {#snippet peekContent()}
      {#if selectedScore}
        <div>
          <h3 class="m-0 text-lg font-semibold text-[#e6edf3]">{selectedScore.name}</h3>
          <p class="mt-1 mb-0 font-mono text-xs text-[#5a6a7a] uppercase tracking-wider">{selectedLabel(selectedScore)}</p>
          <div class="grid grid-cols-3 gap-3 mt-3 py-2 border-y border-[#1e2a3a]">
            <div class="text-center">
              <span class="font-mono text-[0.55rem] tracking-[0.12em] uppercase text-[#5a6a7a]">Heat</span>
              <strong class="block mt-0.5 text-lg leading-none tabular-nums text-[#e6edf3]">{selectedScore.heat.toFixed(0)}</strong>
            </div>
            <div class="text-center">
              <span class="font-mono text-[0.55rem] tracking-[0.12em] uppercase text-[#5a6a7a]">Delta</span>
              <strong class="block mt-0.5 text-lg leading-none tabular-nums text-[#e6edf3]">{formatDelta(selectedScore.delta)}</strong>
            </div>
            <div class="text-center">
              <span class="font-mono text-[0.55rem] tracking-[0.12em] uppercase text-[#5a6a7a]">Conf</span>
              <strong class="block mt-0.5 text-lg leading-none tabular-nums text-[#e6edf3]">{Math.round(selectedScore.confidence * 100)}%</strong>
            </div>
          </div>
        </div>
      {/if}
    {/snippet}

    {#if selectedScore}
      <Inspector score={selectedScore} />
    {/if}
  </MobileBottomSheet>

  <!-- Bottom tab bar -->
  <nav
    class="flex items-center justify-around bg-[#0a0e14] border-t border-[#1e2a3a] shrink-0"
    style="height: calc(56px + env(safe-area-inset-bottom, 0px)); padding-bottom: env(safe-area-inset-bottom, 0px);"
  >
    <!-- Home tab -->
    <button
      type="button"
      class="flex flex-col items-center gap-0.5 pt-1.5 px-4 bg-transparent border-none cursor-pointer"
      onclick={() => activeTab = 'home'}
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={activeTab === 'home' ? '#78d6ff' : '#5a6a7a'} stroke-width="1.5"
      >
        <path d="M3 12l9-9 9 9"/>
        <path d="M5 10v9a1 1 0 001 1h3v-5h6v5h3a1 1 0 001-1v-9"/>
      </svg>
      <span
        class="font-mono text-[0.65rem] tracking-wider uppercase"
        style="color: {activeTab === 'home' ? '#78d6ff' : '#5a6a7a'};"
      >Home</span>
    </button>

    <!-- Map tab -->
    <button
      type="button"
      class="flex flex-col items-center gap-0.5 pt-1.5 px-4 bg-transparent border-none cursor-pointer"
      onclick={() => activeTab = 'map'}
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={activeTab === 'map' ? '#78d6ff' : '#5a6a7a'} stroke-width="1.5"
      >
        <circle cx="12" cy="12" r="10"/>
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10A15.3 15.3 0 0 1 12 2z"/>
      </svg>
      <span
        class="font-mono text-[0.65rem] tracking-wider uppercase"
        style="color: {activeTab === 'map' ? '#78d6ff' : '#5a6a7a'};"
      >Map</span>
    </button>

    <!-- List tab -->
    <button
      type="button"
      class="flex flex-col items-center gap-0.5 pt-1.5 px-4 bg-transparent border-none cursor-pointer"
      onclick={() => activeTab = 'list'}
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={activeTab === 'list' ? '#78d6ff' : '#5a6a7a'} stroke-width="1.5"
      >
        <path d="M12 2L3 7v6c0 5.25 3.75 10.13 9 11.25C17.25 23.13 21 18.25 21 13V7l-9-5z"/>
        <line x1="8" y1="11" x2="16" y2="11"/>
        <line x1="8" y1="15" x2="16" y2="15"/>
      </svg>
      <span
        class="font-mono text-[0.65rem] tracking-wider uppercase"
        style="color: {activeTab === 'list' ? '#78d6ff' : '#5a6a7a'};"
      >List</span>
    </button>
  </nav>
</div>

<style>
  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>
