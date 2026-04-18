<script>
  let { trend = "steady" } = $props();

  const trendClass = $derived(
    trend === "warming" ? "text-amber border-[rgba(255,178,95,0.36)]"
    : trend === "cooling" ? "text-blue border-[rgba(120,214,255,0.36)]"
    : "text-steady border-line"
  );
</script>

<span class="px-3 py-2.5 border font-mono text-xs tracking-[0.14em] uppercase {trendClass}">
  {trend}
</span>
