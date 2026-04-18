<script>
  import { filters, dataset, scraperUrl, wgiUrl, scoringConfig } from "../state.svelte.js";
  import { formatDelta, selectedLabel, buildDetailBrief, recommendedActions } from "../lib/format.js";
  import { fetchWgiForCountry, WGI_DIMENSIONS } from "../lib/wgi.js";
  import TrendPill from "./TrendPill.svelte";
  import Meter from "./Meter.svelte";
  import Sparkline from "./Sparkline.svelte";
  import EvidenceCard from "./EvidenceCard.svelte";

  let { score = null } = $props();

  let wgiData = $state(null);
  let wgiLoading = $state(false);

  /** Extract country name from score — prefer geo.country from evidence, fall back to score.name */
  function resolveCountry(s) {
    if (!s) return null;
    const countries = (s.evidenceBundle ?? [])
      .map(e => e.geo?.country)
      .filter(Boolean);
    return countries[0] ?? s.name;
  }

  $effect(() => {
    const country = resolveCountry(score);
    if (!country || !scoringConfig.wgiEnabled) {
      wgiData = null;
      return;
    }
    wgiLoading = true;
    fetchWgiForCountry(country, wgiUrl.value)
      .then(data => { wgiData = data; wgiLoading = false; })
      .catch(() => { wgiData = { error: 'Service unavailable' }; wgiLoading = false; });
  });

  const brief = $derived.by(() => score ? buildDetailBrief(score, filters.timeWindowHours) : "");
  const actions = $derived.by(() => score ? recommendedActions(score) : []);

  // Try to find an AI summary for the selected location from the dataset or backend
  let fetchedSummaries = $state({});

  // Fetch summaries from backend on mount
  async function fetchSummaries() {
    try {
      const res = await fetch(scraperUrl.value + "/summaries", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        fetchedSummaries = await res.json();
      }
    } catch { /* ignore */ }
  }

  $effect(() => { fetchSummaries(); });

  // Merge dataset.summaries and fetched summaries (backend is fresher)
  const allSummaries = $derived.by(() => {
    return { ...(dataset.summaries ?? {}), ...fetchedSummaries };
  });

  // Find summaries relevant to the selected location.
  // Strategy: check which search IDs (sourceId) produced the evidence for this
  // location, then pull the matching summaries. Fall back to name matching.
  const aiSummary = $derived.by(() => {
    if (!score || !allSummaries) return null;
    const entries = Object.entries(allSummaries);
    if (entries.length === 0) return null;

    // 1. Match via the evidence bundle's sourceId → search ID
    const evidenceSourceIds = new Set(
      (score.evidenceBundle ?? []).map(e => e.sourceId).filter(Boolean)
    );
    for (const [key, text] of entries) {
      if (evidenceSourceIds.has(key)) return text;
    }

    // 2. Fuzzy match: location name against search key or summary text
    const scoreName = score.name.toLowerCase();
    for (const [key, text] of entries) {
      const keyLower = key.toLowerCase().replace(/[-_]/g, " ");
      if (keyLower.includes(scoreName) || scoreName.includes(keyLower)) {
        return text;
      }
    }

    // 3. If only one summary exists, show it as a general brief
    if (entries.length === 1) return entries[0][1];

    return null;
  });

  /** Minimal markdown→HTML renderer with XSS sanitization. */
  function renderMarkdown(src) {
    if (!src) return "";
    // 1. Strip all HTML tags to prevent XSS
    let text = src.replace(/<[^>]*>/g, "");
    // 2. Escape HTML entities in the remaining text
    text = text
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

    // 3. Split into paragraphs on double-newline
    const paragraphs = text.split(/\n{2,}/);

    const rendered = paragraphs.map(para => {
      const trimmed = para.trim();
      if (!trimmed) return "";

      // Check if this paragraph is a list block (all lines start with "- ")
      const lines = trimmed.split("\n");
      const isList = lines.every(l => /^\s*[-*]\s/.test(l));

      if (isList) {
        const items = lines.map(l => {
          let content = l.replace(/^\s*[-*]\s+/, "");
          content = inlineMarkdown(content);
          return `<li>${content}</li>`;
        }).join("");
        return `<ul>${items}</ul>`;
      }

      // Regular paragraph: apply inline formatting, then convert single \n to <br>
      let html = lines.map(l => inlineMarkdown(l)).join("<br>");
      return `<p>${html}</p>`;
    }).join("");

    return rendered;
  }

  /** Convert inline markdown (bold, italic) to HTML. */
  function inlineMarkdown(text) {
    return text
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>");
  }
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

      {#if aiSummary}
        <div class="ai-summary">
          <div class="ai-summary-header">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4zm0 2a2 2 0 0 1 2 2v2H10V6a2 2 0 0 1 2-2zm-3 10a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z" /></svg>
            <span>AI Summary</span>
          </div>
          <div class="ai-summary-text">{@html renderMarkdown(aiSummary)}</div>
        </div>
      {/if}

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

      <div class="grid grid-cols-2 gap-x-5 gap-y-3 mt-4 max-[560px]:grid-cols-1">
        <Meter label="War / Armed conflict" value={score.warComponent} type="war" />
        <Meter label="Military instability" value={score.militaryComponent} type="military" />
        <Meter label="Civil unrest" value={score.civilComponent} type="civil" />
        <Meter label="Terrorism / Insurgency" value={score.terrorismComponent} type="terrorism" />
        <Meter label="Humanitarian crisis" value={score.humanitarianComponent} type="humanitarian" />
        <Meter label="Information warfare" value={score.infowarComponent} type="infowar" />
      </div>

      {#if scoringConfig.wgiEnabled}
        <div class="pt-4 mt-4 border-t border-line">
          <div class="flex items-center gap-3 mb-3">
            <span class="section-flag">Governance Indicators (World Bank WGI)</span>
            <hr class="rule-thin flex-1" />
          </div>
          {#if wgiLoading}
            <p class="m-0 text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">Loading governance data...</p>
          {:else if wgiData?.error}
            <p class="m-0 text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">Governance data unavailable — {wgiData.error}</p>
          {:else if wgiData && Object.keys(wgiData).length > 0}
            <div class="grid grid-cols-2 gap-x-5 gap-y-3 max-[560px]:grid-cols-1">
              {#each WGI_DIMENSIONS as dim}
                {#if wgiData[dim.key]}
                  <Meter
                    label="{dim.label} ({wgiData[dim.key].year})"
                    value={wgiData[dim.key].value}
                    type="governance"
                  />
                {/if}
              {/each}
            </div>
          {:else}
            <p class="m-0 text-muted font-mono text-[0.72rem] tracking-[0.08em] uppercase">No governance data available</p>
          {/if}
        </div>
      {/if}

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

<style>
  .ai-summary {
    margin-top: 12px;
    padding: 12px 14px;
    background: rgba(120, 214, 255, 0.04);
    border: 1px solid rgba(120, 214, 255, 0.15);
    border-radius: 4px;
  }
  .ai-summary-header {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #78d6ff;
    margin-bottom: 6px;
  }
  .ai-summary-text {
    margin: 0;
    font-size: 0.85rem;
    line-height: 1.6;
    color: var(--color-detail-light, rgba(255, 255, 255, 0.78));
  }
  .ai-summary-text :global(p) {
    margin: 0 0 0.5em;
  }
  .ai-summary-text :global(p:last-child) {
    margin-bottom: 0;
  }
  .ai-summary-text :global(ul) {
    margin: 0.3em 0 0.5em;
    padding-left: 1.2em;
  }
  .ai-summary-text :global(li) {
    margin-bottom: 0.2em;
  }
</style>
