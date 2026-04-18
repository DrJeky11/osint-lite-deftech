<script>
  let { hotspots = 0, signals = 0, sources = 0, window: windowLabel = "24h" } = $props();
</script>

<section class="grid grid-cols-4 max-[680px]:grid-cols-2 max-[400px]:grid-cols-1" aria-label="Watchfloor summary">
  <div class="flex items-center justify-center gap-3 py-3 px-4 border-r border-line max-[680px]:border-b max-[400px]:border-r-0">
    <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-muted">Theaters</span>
    <strong class="text-2xl leading-none tabular-nums">{hotspots}</strong>
  </div>
  <div class="flex items-center justify-center gap-3 py-3 px-4 border-r border-line max-[680px]:border-r-0 max-[680px]:border-b">
    <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-muted">Signals</span>
    <strong class="text-2xl leading-none tabular-nums">{signals}</strong>
  </div>
  <div class="flex items-center justify-center gap-3 py-3 px-4 border-r border-line max-[680px]:border-b">
    <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-muted">Sources</span>
    <strong class="text-2xl leading-none tabular-nums">{sources}</strong>
  </div>
  <div class="flex items-center justify-center gap-3 py-3 px-4">
    <span class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-muted">Window</span>
    <strong class="text-2xl leading-none tabular-nums">{windowLabel}</strong>
  </div>
</section>
