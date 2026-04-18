<script>
  import {
    OVERLAY_REGISTRY,
    OVERLAY_CATEGORIES,
    loadOverlayPreferences,
    saveOverlayPreference,
  } from "../lib/overlays.js";

  let { onToggle = () => {} } = $props();

  let prefs = $state(loadOverlayPreferences());
  let searchQuery = $state("");
  let activeCategory = $state("all");
  let open = $state(false);

  const CATEGORY_COLORS = {
    military: "#ef4444",
    infrastructure: "#facc15",
    maritime: "#0ea5e9",
    air: "#a855f7",
    ground: "#22d3ee",
    geopolitical: "#fb923c",
    humanitarian: "#f472b6",
    hazard: "#ef4444",
  };

  const filteredOverlays = $derived.by(() => {
    let results = OVERLAY_REGISTRY;

    if (activeCategory !== "all") {
      results = results.filter((o) => o.category === activeCategory);
    }

    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      results = results.filter(
        (o) => o.label.toLowerCase().includes(q) || o.desc.toLowerCase().includes(q)
      );
    }

    return results;
  });

  const activeCount = $derived(
    OVERLAY_REGISTRY.filter((o) => prefs[o.id]).length
  );

  const allFilteredOn = $derived(
    filteredOverlays.length > 0 && filteredOverlays.every((o) => prefs[o.id])
  );

  function toggle(id) {
    prefs[id] = !prefs[id];
    saveOverlayPreference(id, prefs[id]);
    onToggle(id, prefs[id]);
  }

  function enableAll() {
    for (const overlay of filteredOverlays) {
      if (!prefs[overlay.id]) {
        prefs[overlay.id] = true;
        saveOverlayPreference(overlay.id, true);
        onToggle(overlay.id, true);
      }
    }
  }

  function disableAll() {
    for (const overlay of filteredOverlays) {
      if (prefs[overlay.id]) {
        prefs[overlay.id] = false;
        saveOverlayPreference(overlay.id, false);
        onToggle(overlay.id, false);
      }
    }
  }
</script>

<section class="border border-line">
  <!-- Header bar — always visible, acts as toggle -->
  <button
    type="button"
    class="w-full flex items-center gap-3 px-4 py-2.5 bg-panel-soft cursor-pointer border-0 text-left transition-colors hover:bg-[rgba(12,21,34,0.85)]"
    onclick={() => (open = !open)}
  >
    <span class="section-flag">Overlay Layers</span>
    {#if activeCount > 0}
      <span class="font-mono text-[0.6rem] tracking-[0.1em] text-blue">{activeCount} active</span>
    {/if}
    <hr class="rule-thin flex-1" />
    <span class="font-mono text-[0.6rem] tracking-[0.1em] uppercase text-muted shrink-0">
      {open ? "Minimize" : "Expand"}
    </span>
    <span class="text-muted text-[0.7rem] transition-transform duration-200 shrink-0" class:rotate-180={open}>&#9660;</span>
  </button>

  <!-- Collapsible body -->
  {#if open}
    <div class="border-t border-line px-4 py-3">
      <!-- Search + Category bar -->
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <div class="relative min-w-[200px] flex-shrink-0">
          <input
            type="text"
            placeholder="Search layers..."
            bind:value={searchQuery}
            class="w-full border border-line bg-panel-strong text-text font-mono text-[0.75rem] px-3 py-2 pr-8 placeholder:text-muted/60 focus:outline-1 focus:outline-blue/30 focus:outline-offset-1"
          />
          {#if searchQuery}
            <button
              type="button"
              onclick={() => (searchQuery = "")}
              class="absolute right-2 top-1/2 -translate-y-1/2 text-muted hover:text-text text-xs cursor-pointer bg-transparent border-0 p-0"
              aria-label="Clear search"
            >&times;</button>
          {/if}
        </div>

        <div class="flex flex-wrap gap-1">
          <button
            type="button"
            class="px-2.5 py-1.5 border font-mono text-[0.6rem] tracking-[0.12em] uppercase cursor-pointer transition-colors"
            class:bg-[rgba(120,214,255,0.1)]={activeCategory === "all"}
            class:border-[rgba(120,214,255,0.3)]={activeCategory === "all"}
            class:text-blue={activeCategory === "all"}
            class:bg-transparent={activeCategory !== "all"}
            class:border-line={activeCategory !== "all"}
            class:text-muted={activeCategory !== "all"}
            class:hover:text-text={activeCategory !== "all"}
            onclick={() => (activeCategory = "all")}
          >All</button>

          {#each OVERLAY_CATEGORIES as cat}
            <button
              type="button"
              class="flex items-center gap-1.5 px-2.5 py-1.5 border font-mono text-[0.6rem] tracking-[0.12em] uppercase cursor-pointer transition-colors"
              class:bg-[rgba(120,214,255,0.1)]={activeCategory === cat.key}
              class:border-[rgba(120,214,255,0.3)]={activeCategory === cat.key}
              class:text-blue={activeCategory === cat.key}
              class:bg-transparent={activeCategory !== cat.key}
              class:border-line={activeCategory !== cat.key}
              class:text-muted={activeCategory !== cat.key}
              class:hover:text-text={activeCategory !== cat.key}
              onclick={() => (activeCategory = cat.key)}
            >
              <span class="w-1.5 h-1.5 rounded-full shrink-0" style="background: {CATEGORY_COLORS[cat.key]}"></span>
              {cat.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Enable / Disable all -->
      {#if filteredOverlays.length > 0}
        <div class="flex items-center gap-2 mb-3">
          <button
            type="button"
            class="px-2.5 py-1.5 border border-line font-mono text-[0.6rem] tracking-[0.1em] uppercase cursor-pointer transition-colors text-muted hover:text-civil hover:border-civil/40 disabled:opacity-30 disabled:cursor-default"
            onclick={enableAll}
            disabled={allFilteredOn}
          >Enable all</button>
          <button
            type="button"
            class="px-2.5 py-1.5 border border-line font-mono text-[0.6rem] tracking-[0.1em] uppercase cursor-pointer transition-colors text-muted hover:text-military hover:border-military/40 disabled:opacity-30 disabled:cursor-default"
            onclick={disableAll}
            disabled={activeCount === 0}
          >Disable all</button>
          {#if activeCategory !== "all"}
            <span class="font-mono text-[0.55rem] tracking-[0.08em] text-muted/60">(applies to {filteredOverlays.length} filtered)</span>
          {/if}
        </div>
      {/if}

      <!-- Overlay grid -->
      {#if filteredOverlays.length === 0}
        <p class="m-0 py-6 text-center text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">No layers match your search</p>
      {:else}
        <div class="grid grid-cols-3 gap-px bg-line max-[1100px]:grid-cols-2 max-[560px]:grid-cols-1">
          {#each filteredOverlays as overlay}
            <button
              type="button"
              class="grid gap-1.5 text-left p-4 bg-bg transition-all duration-150 cursor-pointer"
              class:overlay-active={prefs[overlay.id]}
              class:hover:bg-[rgba(120,214,255,0.02)]={!prefs[overlay.id]}
              onclick={() => toggle(overlay.id)}
            >
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full shrink-0" style="background: {CATEGORY_COLORS[overlay.category]}; opacity: {prefs[overlay.id] ? 1 : 0.4}"></span>
                <span class="text-[0.85rem] font-semibold leading-tight">{overlay.label}</span>
                {#if prefs[overlay.id]}
                  <span class="ml-auto font-mono text-[0.55rem] tracking-[0.1em] uppercase text-blue">On</span>
                {/if}
              </div>
              <p class="m-0 text-[0.75rem] text-muted leading-snug pl-4">{overlay.desc}</p>
              <span class="font-mono text-[0.55rem] tracking-[0.1em] uppercase text-muted/60 pl-4">{overlay.category} &middot; {overlay.layerType}</span>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</section>

<style>
  .overlay-active {
    background: rgba(120, 214, 255, 0.04);
    box-shadow: inset 3px 0 0 rgba(120, 214, 255, 0.5);
  }
</style>
