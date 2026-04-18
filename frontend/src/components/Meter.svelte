<script>
  import { scoringConfig } from "../state.svelte.js";

  let { label = "", value = 0, type = "civil" } = $props();

  const GRADIENTS = {
    war: "linear-gradient(90deg, rgba(239, 68, 68, 0.22), #ef4444)",
    military: "linear-gradient(90deg, rgba(255, 117, 87, 0.22), #ff7557)",
    civil: "linear-gradient(90deg, rgba(73, 212, 186, 0.22), #49d4ba)",
    terrorism: "linear-gradient(90deg, rgba(167, 139, 250, 0.22), #a78bfa)",
    humanitarian: "linear-gradient(90deg, rgba(255, 178, 95, 0.22), #ffb25f)",
    infowar: "linear-gradient(90deg, rgba(120, 214, 255, 0.22), #78d6ff)",
    governance: "linear-gradient(90deg, rgba(56, 189, 248, 0.22), #38bdf8)",
  };
  const barGradient = $derived(GRADIENTS[type] ?? GRADIENTS.civil);
  const displayMax = $derived(scoringConfig.componentDisplayMax ?? 100);
  const barPct = $derived(Math.min(100, (value / displayMax) * 100));
  const isOverflow = $derived(value > displayMax);
</script>

<div>
  <div class="flex justify-between gap-3.5 mb-1.5 text-split-label font-mono text-xs tracking-[0.09em] uppercase">
    <span>{label}</span>
    <span>{value.toFixed(0)}{#if isOverflow}<span class="text-[0.65rem] opacity-60 ml-0.5" title="Exceeds normal range">!</span>{/if}</span>
  </div>
  <div class="h-2.5 bg-[rgba(255,255,255,0.05)] overflow-hidden relative">
    <span
      class="block h-full"
      style="width: {barPct}%; background: {barGradient}"
    ></span>
    {#if isOverflow}
      <span class="absolute right-0 top-0 h-full w-1" style="background: {GRADIENTS[type]?.split(', ').pop()?.replace(')', '') ?? '#fff'}; opacity: 0.9"></span>
    {/if}
  </div>
</div>
