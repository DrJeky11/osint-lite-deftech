<script>
  let { label = "", value = 0, type = "civil" } = $props();

  const barGradient = $derived(type === "civil"
    ? "linear-gradient(90deg, rgba(73, 212, 186, 0.22), var(--color-civil))"
    : "linear-gradient(90deg, rgba(255, 117, 87, 0.22), var(--color-military))");
</script>

<div>
  <div class="flex justify-between gap-3.5 mb-1.5 text-split-label font-mono text-xs tracking-[0.09em] uppercase">
    <span>{label}</span>
    <span>{value.toFixed(0)}</span>
  </div>
  <div class="h-2.5 bg-[rgba(255,255,255,0.05)] overflow-hidden">
    <span
      class="block h-full"
      style="width: {Math.min(100, value)}%; background: {barGradient}"
    ></span>
  </div>
</div>
