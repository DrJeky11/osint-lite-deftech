<script>
  import {
    OVERLAY_REGISTRY,
    OVERLAY_CATEGORIES,
    loadOverlayPreferences,
    saveOverlayPreference,
  } from "../lib/overlays.js";

  let { onToggle = () => {} } = $props();

  let open = $state(false);
  let prefs = $state(loadOverlayPreferences());

  const activeCount = $derived(
    OVERLAY_REGISTRY.filter((o) => prefs[o.id]).length
  );

  function toggle(id) {
    prefs[id] = !prefs[id];
    saveOverlayPreference(id, prefs[id]);
    onToggle(id, prefs[id]);
  }

  function overlaysInCategory(catKey) {
    return OVERLAY_REGISTRY.filter((o) => o.category === catKey);
  }
</script>

<div class="absolute bottom-3 left-3 z-10 pointer-events-auto">
  <button
    type="button"
    onclick={() => (open = !open)}
    class="flex items-center gap-1.5 px-3 py-2 border border-line bg-[rgba(3,8,15,0.85)] backdrop-blur-md text-text text-xs font-mono tracking-[0.08em] uppercase cursor-pointer hover:border-[rgba(120,214,255,0.32)] transition-colors"
    class:border-[rgba(120,214,255,0.4)]={open}
  >
    Layers
    {#if activeCount > 0}
      <span class="inline-flex items-center justify-center min-w-5 h-5 px-1.5 rounded-full bg-blue/20 text-blue text-[10px] font-bold leading-none">
        {activeCount}
      </span>
    {/if}
  </button>

  {#if open}
    <div class="absolute bottom-full left-0 mb-2 w-[320px] max-h-[480px] overflow-y-auto border border-line bg-[rgba(6,12,22,0.95)] backdrop-blur-xl shadow-panel">
      <div class="px-4 pt-4 pb-2 border-b border-line">
        <h4 class="m-0 text-sm font-semibold text-text">Overlay Layers</h4>
        <p class="m-0 mt-1 font-mono text-[10px] tracking-[0.1em] uppercase text-muted">
          Toggle infrastructure and reference data
        </p>
      </div>

      <div class="p-3 grid gap-3">
        {#each OVERLAY_CATEGORIES as cat}
          {@const items = overlaysInCategory(cat.key)}
          {#if items.length > 0}
            <div>
              <p class="m-0 mb-1.5 font-mono text-[10px] tracking-[0.14em] uppercase text-muted">{cat.label}</p>
              <div class="grid gap-1">
                {#each items as overlay}
                  <label
                    class="flex items-start gap-2.5 p-2.5 rounded-md cursor-pointer transition-colors"
                    class:bg-[rgba(120,214,255,0.06)]={prefs[overlay.id]}
                    class:hover:bg-[rgba(120,214,255,0.04)]={!prefs[overlay.id]}
                  >
                    <input
                      type="checkbox"
                      checked={prefs[overlay.id]}
                      onchange={() => toggle(overlay.id)}
                      class="mt-0.5 w-4 h-4 accent-[var(--color-blue)] cursor-pointer shrink-0"
                    />
                    <div class="grid gap-0.5 min-w-0">
                      <span class="text-[13px] text-text leading-tight">{overlay.label}</span>
                      <span class="text-[11px] text-muted leading-snug">{overlay.desc}</span>
                    </div>
                  </label>
                {/each}
              </div>
            </div>
          {/if}
        {/each}
      </div>
    </div>
  {/if}
</div>
