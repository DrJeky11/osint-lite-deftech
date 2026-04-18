<script>
  import { dataset } from "../state.svelte.js";
  import { unique } from "../lib/format.js";

  const now = new Date(dataset.generatedAt);
  const dateStr = now.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric"
  });
  const timeStr = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  });

  const editionNumber = `VOL. ${now.getFullYear()}.${String(now.getMonth() + 1).padStart(2, "0")}.${String(now.getDate()).padStart(2, "0")}`;

  const sourceCatalog = dataset.sourceCatalog?.length ? dataset.sourceCatalog : dataset.feedCatalog ?? [];
  let sourceSummary = "Awaiting source telemetry";
  if (sourceCatalog.length) {
    const sources = unique(sourceCatalog.map((entry) => entry.source));
    sourceSummary = `${sources.slice(0, 4).join(" \u00b7 ")} + ${Math.max(0, sourceCatalog.length - 4)} more`;
    if (dataset.sourceStatus?.bluesky !== "loaded") {
      sourceSummary += " \u00b7 Bluesky offline";
    }
  } else if (dataset.failures?.length) {
    sourceSummary = "Live refresh failed \u2014 operating from cache";
  }
</script>

<header class="animate-[shell-in_720ms_ease_both]">
  <!-- Top rule -->
  <hr class="rule-heavy" />

  <!-- Nameplate -->
  <div class="py-4 text-center">
    <p class="m-0 font-mono text-[0.6rem] tracking-[0.3em] uppercase text-muted">{editionNumber}</p>
    <h1 class="m-0 mt-1.5 tracking-[0.12em] uppercase text-[clamp(2.6rem,7vw,5.2rem)] leading-none font-light">
      Signal Atlas
    </h1>
    <p class="m-0 mt-1 headline-editorial text-[clamp(0.85rem,1.8vw,1.15rem)] text-muted">
      Open-Source Intelligence Watchfloor
    </p>
  </div>

  <hr class="rule-double" />

  <!-- Dateline bar -->
  <div class="flex justify-between items-center gap-4 px-4 py-2 max-[680px]:flex-col max-[680px]:text-center">
    <div class="flex items-center gap-3">
      <span
        class="w-2 h-2 rounded-full bg-civil shrink-0"
        style="box-shadow: 0 0 0 4px rgba(73, 212, 186, 0.1), 0 0 16px rgba(73, 212, 186, 0.4); animation: ticker-pulse 2.4s ease-in-out infinite"
        aria-hidden="true"
      ></span>
      <span class="font-mono text-[0.7rem] tracking-[0.08em] uppercase text-edition">Live snapshot {timeStr} UTC</span>
    </div>
    <span class="font-mono text-[0.7rem] tracking-[0.08em] uppercase text-muted">{dateStr}</span>
    <span class="font-mono text-[0.65rem] tracking-[0.06em] text-muted max-w-[320px] text-right truncate max-[680px]:text-center">{sourceSummary}</span>
  </div>

  <hr class="rule-thin" />
</header>
