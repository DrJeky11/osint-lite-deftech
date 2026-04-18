<script>
  import { filters, selection, getVisibleScores, getFilteredSignalEvents, getSelectedScore, ensureValidSelection } from "./state.svelte.js";
  import { unique } from "./lib/format.js";
  import Masthead from "./components/Masthead.svelte";
  import MetricsGrid from "./components/MetricsGrid.svelte";
  import MapStage from "./components/MapStage.svelte";
  import ControlDock from "./components/ControlDock.svelte";
  import HotspotList from "./components/HotspotList.svelte";
  import Inspector from "./components/Inspector.svelte";
  import OverlayPanel from "./components/OverlayPanel.svelte";
  import MobileShell from "./components/MobileShell.svelte";
  import RegionalSummaryCards from "./components/RegionalSummaryCards.svelte";
  import AdminPage from "./components/AdminPage.svelte";

  let currentView = $state("watchfloor");

  let innerWidth = $state(0);
  let isMobile = $derived(innerWidth < 768);

  let mapStage;
  let visibleScores = $state([]);
  let filteredEvents = $state([]);

  const selectedScore = $derived(getSelectedScore(visibleScores));

  const sourceCount = $derived(
    unique(filteredEvents.map((e) => e.sourceName ?? e.sourceFamily ?? e.source)).length
  );

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

  function handleHotspotSelect(scoreId) {
    mapStage?.selectHotspot(scoreId);
  }

  function handleOverlayToggle(id, visible) {
    mapStage?.handleOverlayToggle(id, visible);
  }

</script>

<svelte:window bind:innerWidth />

{#if !isMobile}
<!-- ═══ TOP NAV ═══ -->
<nav class="sa-nav">
  <div class="w-[min(1560px,calc(100vw-32px))] mx-auto flex items-center justify-between">
    <span class="sa-nav-brand">Signal Atlas</span>
    <div class="sa-nav-links">
      <button
        type="button"
        class="sa-nav-link"
        class:sa-nav-active={currentView === "watchfloor"}
        onclick={() => currentView = "watchfloor"}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        Watchfloor
      </button>
      <button
        type="button"
        class="sa-nav-link"
        class:sa-nav-active={currentView === "admin"}
        onclick={() => currentView = "admin"}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
        Admin
      </button>
    </div>
  </div>
</nav>

{#if currentView === "admin"}
<AdminPage onBack={() => currentView = "watchfloor"} />
{:else}
<div class="w-[min(1560px,calc(100vw-32px))] mx-auto py-5 pb-8 animate-[shell-in_720ms_ease_both]">

  <!-- ═══ NAMEPLATE ═══ -->
  <Masthead />

  <!-- ═══ METRICS RIBBON ═══ -->
  <div class="border-x border-b border-line bg-panel-soft mb-4">
    <MetricsGrid
      hotspots={visibleScores.length}
      signals={filteredEvents.length}
      sources={sourceCount}
      window="{filters.timeWindowHours}h"
    />
  </div>

  <hr class="rule-heavy mt-0" />

  <!-- ═══ LEAD STORY: MAP + INSPECTOR ═══ -->
  <main class="grid grid-cols-[minmax(0,1fr)_minmax(340px,420px)] gap-0 mt-4 max-[1100px]:grid-cols-1">

    <!-- Left column: Situation Room -->
    <section class="pr-5 max-[1100px]:pr-0">
      <div class="flex items-center gap-3 mb-3">
        <span class="section-flag">Situation Room</span>
        <hr class="rule-thin flex-1" />
      </div>

      <p class="m-0 mb-4 headline-editorial text-[clamp(1.1rem,2vw,1.45rem)] max-w-[52ch] leading-[1.45]">
        Where civil unrest and force stress are rising before the feed backlog hides it.
      </p>

      <MapStage bind:this={mapStage} onDataUpdate={handleDataUpdate} />

      <div class="mt-4">
        <ControlDock onFilterChange={handleFilterChange} onProjectionChange={handleProjectionChange} />
      </div>

      <!-- Overlay Layers -->
      <div class="mt-4">
        <OverlayPanel onToggle={handleOverlayToggle} />
      </div>

      <!-- Priority Theaters -->
      <div class="mt-6">
        <div class="flex items-center gap-3 mb-3">
          <span class="section-flag">Priority Theaters</span>
          <hr class="rule-thin flex-1" />
        </div>
        <HotspotList {visibleScores} onSelect={handleHotspotSelect} />
      </div>

      <!-- Regional Summary Cards -->
      <RegionalSummaryCards {visibleScores} {filteredEvents} onHotspotSelect={handleHotspotSelect} />
    </section>

    <!-- Right column: Intelligence Brief -->
    <section class="col-divider pl-5 max-[1100px]:border-l-0 max-[1100px]:pl-0 max-[1100px]:mt-6 max-[1100px]:pt-6 max-[1100px]:border-t max-[1100px]:border-line">
      <div class="flex items-center gap-3 mb-3">
        <span class="section-flag">Intelligence Brief</span>
        <hr class="rule-thin flex-1" />
      </div>
      <Inspector score={selectedScore} />
    </section>
  </main>

  <!-- ═══ FOOTER RULE ═══ -->
  <hr class="rule-double mt-8" />
  <p class="m-0 mt-2 text-center font-mono text-[0.58rem] tracking-[0.2em] uppercase text-muted">
    Signal Atlas &middot; Open-source intelligence watchfloor &middot; All data derived from public sources
  </p>
</div>
{/if}
{:else}
<MobileShell />
{/if}
