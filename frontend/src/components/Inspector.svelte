<script>
  import { filters } from "../state.svelte.js";
  import { formatDelta, selectedLabel, buildDetailBrief, recommendedActions } from "../lib/format.js";
  import TrendPill from "./TrendPill.svelte";
  import Meter from "./Meter.svelte";
  import Sparkline from "./Sparkline.svelte";
  import EvidenceCard from "./EvidenceCard.svelte";

  let { score = null } = $props();

  const brief = $derived.by(() => score ? buildDetailBrief(score, filters.timeWindowHours) : "");
  const actions = $derived.by(() => score ? recommendedActions(score) : []);
</script>

<aside class="grid content-start gap-0">
  <!-- Detail Summary -->
  <section>
    {#if score}
      <div class="flex justify-between gap-3 items-start max-[820px]:grid">
        <div>
          <h3 class="m-0 tracking-[-0.02em] leading-[0.96] text-[clamp(1.8rem,2.8vw,2.8rem)]">{score.name}</h3>
          <p class="mt-2 mb-0 headline-editorial text-[0.95rem] text-detail-light leading-[1.55]">{brief}</p>
        </div>
        <TrendPill trend={selectedLabel(score)} />
      </div>

      <div class="grid grid-cols-3 gap-4 mt-4 py-4 border-y border-line max-[820px]:grid-cols-2 max-[560px]:grid-cols-1">
        <div class="text-center">
          <span class="metric-label">Heat</span>
          <strong class="block mt-1 text-[clamp(1.6rem,2vw,2.4rem)] leading-none tabular-nums">{score.heat.toFixed(0)}</strong>
        </div>
        <div class="text-center">
          <span class="metric-label">Delta</span>
          <strong class="block mt-1 text-[clamp(1.6rem,2vw,2.4rem)] leading-none tabular-nums">{formatDelta(score.delta)}</strong>
        </div>
        <div class="text-center">
          <span class="metric-label">Confidence</span>
          <strong class="block mt-1 text-[clamp(1.6rem,2vw,2.4rem)] leading-none tabular-nums">{Math.round(score.confidence * 100)}%</strong>
        </div>
      </div>

      <div class="grid gap-3 mt-4">
        <Meter label="Civil unrest" value={score.civilComponent} type="civil" />
        <Meter label="Military instability" value={score.militaryComponent} type="military" />
      </div>

      <div class="mt-4">
        <Sparkline history={score.history} />
      </div>
    {:else}
      <h3 class="m-0 tracking-[-0.02em] leading-[0.96] text-[clamp(1.8rem,2.8vw,2.8rem)]">No active theater</h3>
      <p class="mt-2 mb-0 headline-editorial text-[0.95rem] text-detail-light leading-[1.55]">Adjust filters to surface an active location.</p>
    {/if}
  </section>

  <!-- Top Drivers -->
  <section class="pt-5 mt-5 border-t border-line">
    <div class="flex items-center gap-3 mb-3">
      <span class="section-flag">Drivers</span>
      <hr class="rule-thin flex-1" />
    </div>
    <ul class="flex flex-wrap gap-2 list-none p-0 m-0">
      {#if score}
        {#each score.topDrivers as driver}
          <li class="px-2.5 py-2 border border-line text-tag-text text-[0.82rem] bg-[rgba(255,255,255,0.02)]">{driver}</li>
        {/each}
      {/if}
    </ul>
  </section>

  <!-- Evidence Bundle -->
  <section class="pt-5 mt-5 border-t border-line">
    <div class="flex items-center gap-3 mb-3">
      <span class="section-flag">Evidence</span>
      <hr class="rule-thin flex-1" />
    </div>
    <div class="grid">
      {#if score && score.evidenceBundle.length > 0}
        {#each score.evidenceBundle as event}
          <EvidenceCard {event} />
        {/each}
      {:else}
        <p class="m-0 text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">No corroborating items</p>
      {/if}
    </div>
  </section>

  <!-- Next-step Collection -->
  <section class="pt-5 mt-5 border-t border-line">
    <div class="flex items-center gap-3 mb-3">
      <span class="section-flag">Collection Tasks</span>
      <hr class="rule-thin flex-1" />
    </div>
    <ul class="grid gap-2.5 list-none p-0 m-0">
      {#each actions as action}
        <li class="relative pl-4 text-evidence-body text-[0.88rem] leading-[1.6]">
          <span class="absolute left-0 top-[0.6rem] w-1.5 h-1.5 rounded-full bg-amber" style="box-shadow: 0 0 12px rgba(255, 178, 95, 0.4)"></span>
          {action}
        </li>
      {/each}
    </ul>
  </section>
</aside>
