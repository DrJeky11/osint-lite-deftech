<script>
  import { filters, selection, getVisibleScores, getFilteredSignalEvents, getSelectedScore, ensureValidSelection } from "./state.svelte.js";
  import { unique } from "./lib/format.js";
  import Masthead from "./components/Masthead.svelte";
  import MetricsGrid from "./components/MetricsGrid.svelte";
  import MapStage from "./components/MapStage.svelte";
  import ControlDock from "./components/ControlDock.svelte";
  import HotspotList from "./components/HotspotList.svelte";
  import Inspector from "./components/Inspector.svelte";

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
</script>

<div class="w-[min(1560px,calc(100vw-32px))] mx-auto py-5 pb-8 animate-[shell-in_720ms_ease_both]">

  <!-- ═══ NAMEPLATE ═══ -->
  <Masthead />

  <!-- ═══ METRICS RIBBON ═══ -->
  <div class="border-x border-b border-line bg-panel-soft">
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

      <!-- Priority Theaters -->
      <div class="mt-6">
        <div class="flex items-center gap-3 mb-3">
          <span class="section-flag">Priority Theaters</span>
          <hr class="rule-thin flex-1" />
        </div>
        <HotspotList {visibleScores} onSelect={handleHotspotSelect} />
      </div>
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
