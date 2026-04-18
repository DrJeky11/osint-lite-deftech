<script>
  import { formatHoursAgo } from "../lib/format.js";

  let { event } = $props();

  const authorName = $derived(event.author?.handle ? `@${event.author.handle}` : event.author?.name ?? event.sourceName);
</script>

<article class="grid gap-1.5 py-3.5 border-t border-line first:pt-0 first:border-t-0">
  <div class="flex justify-between gap-3 text-muted font-mono text-[0.6rem] tracking-[0.14em] uppercase">
    <span>{event.sourceFamily}</span>
    <span>{formatHoursAgo(event.timestamp)}</span>
  </div>
  <h4 class="m-0 text-[0.9rem] leading-[1.4] font-semibold">
    {#if event.url}
      <a href={event.url} target="_blank" rel="noreferrer"
        class="no-underline border-b border-[rgba(255,255,255,0.12)] hover:border-amber transition-colors"
      >{event.title}</a>
    {:else}
      {event.title}
    {/if}
  </h4>
  <p class="m-0 text-evidence-body text-[0.82rem] leading-[1.55]">{event.excerpt}</p>
  <footer class="text-muted font-mono text-[0.58rem] tracking-[0.1em] uppercase">
    {authorName} &middot; {event.geo.name} &middot; {Math.round(event.geo.confidence * 100)}% &middot; {event.classification.signalType}
  </footer>
</article>
