<script>
  let { history = [] } = $props();

  function computePath(data) {
    if (!data.length) return { polyline: "", area: "", lastPoint: null };
    const maxValue = Math.max(...data, 1);
    const points = data.map((value, index) => ({
      x: index * (240 / Math.max(data.length - 1, 1)),
      y: 68 - (value / maxValue) * 54
    }));
    const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");
    const area = `0,72 ${polyline} 240,72`;
    return { polyline, area, lastPoint: points.at(-1) };
  }

  const path = $derived(computePath(history));
</script>

<div class="grid gap-2">
  <p class="metric-label">Heat trend</p>
  <svg viewBox="0 0 240 72" aria-hidden="true"
    class="w-full h-[76px]"
    style="background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012))"
  >
    {#if path.lastPoint}
      <defs>
        <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255, 178, 95, 0.42)" />
          <stop offset="100%" stop-color="rgba(255, 178, 95, 0)" />
        </linearGradient>
      </defs>
      <polygon fill="url(#spark-fill)" points={path.area} />
      <polyline
        fill="none"
        stroke="rgba(255, 178, 95, 0.95)"
        stroke-width="3"
        points={path.polyline}
        stroke-linecap="round"
        stroke-linejoin="round"
      />
      <circle
        cx={path.lastPoint.x}
        cy={path.lastPoint.y}
        r="4"
        fill="rgba(255, 245, 232, 0.96)"
        stroke="rgba(255, 178, 95, 0.88)"
        stroke-width="2"
      />
    {/if}
  </svg>
</div>
