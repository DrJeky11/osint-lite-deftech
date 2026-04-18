<script>
  import { onMount } from "svelte";

  const STORAGE_KEY = "sa-scraper-config";

  /* ── State ── */
  let topics = $state("");
  let location = $state("");
  let startDate = $state("");
  let endDate = $state("");
  let question = $state("");
  let maxArticles = $state(20);

  let loading = $state(false);
  let error = $state("");
  let result = $state(null);
  let backendStatus = $state("checking"); // "checking" | "connected" | "unreachable"

  let baseUrl = $derived.by(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return stored.replace(/\/+$/, "");
    } catch {}
    return "http://localhost:8000";
  });

  /* ── Health check on mount ── */
  onMount(() => {
    checkHealth();
  });

  async function checkHealth() {
    backendStatus = "checking";
    try {
      const res = await fetch(`${baseUrl}/health`, {
        signal: AbortSignal.timeout(5000),
      });
      backendStatus = res.ok ? "connected" : "unreachable";
    } catch {
      backendStatus = "unreachable";
    }
  }

  /* ── Build request body ── */
  function buildRequest() {
    const topicList = topics
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    if (topicList.length === 0) {
      throw new Error("At least one topic is required.");
    }
    const body = { topics: topicList, max_articles: maxArticles };
    if (location.trim()) body.location = location.trim();
    if (startDate) body.start_date = startDate;
    if (endDate) body.end_date = endDate;
    if (question.trim()) body.question = question.trim();
    return body;
  }

  /* ── Fetch helpers ── */
  async function fetchArticles() {
    await doFetch("/articles");
  }

  async function fetchAndSummarize() {
    await doFetch("/summarize");
  }

  async function doFetch(endpoint) {
    error = "";
    result = null;
    let body;
    try {
      body = buildRequest();
    } catch (e) {
      error = e.message;
      return;
    }
    loading = true;
    try {
      const res = await fetch(`${baseUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(60000),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
      }
      result = await res.json();
    } catch (e) {
      error = e.name === "TimeoutError" ? "Request timed out (60s)" : e.message;
    } finally {
      loading = false;
    }
  }

  /* ── Helpers ── */
  function truncate(str, len = 180) {
    if (!str) return "";
    return str.length > len ? str.slice(0, len) + "..." : str;
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateStr;
    }
  }
</script>

<div class="news-search-panel">
  <!-- Header -->
  <div class="flex items-center gap-3 mb-1">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-blue">
      <path d="M4 4h16v2H4zM4 9h16v2H4zM4 14h10v2H4z" />
    </svg>
    <h2 class="m-0 text-[1.05rem] font-semibold tracking-tight">News Search</h2>
    <!-- Connection status -->
    <div class="flex items-center gap-2 ml-auto">
      <span
        class="inline-block w-[7px] h-[7px] rounded-full"
        class:status-connected={backendStatus === "connected"}
        class:status-unreachable={backendStatus === "unreachable"}
        class:status-checking={backendStatus === "checking"}
      ></span>
      <span class="font-mono text-[0.58rem] tracking-[0.1em] uppercase text-muted">
        {#if backendStatus === "checking"}
          Checking...
        {:else if backendStatus === "connected"}
          Scraper Online
        {:else}
          Scraper Offline
        {/if}
      </span>
      <button
        type="button"
        class="action-btn"
        style="padding: 3px 6px; min-width: unset;"
        onclick={checkHealth}
        title="Re-check connection"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
      </button>
    </div>
  </div>
  <p class="m-0 mb-4 text-[0.78rem] text-muted">Search and summarize news articles via the scraper backend.</p>

  <!-- Search Form -->
  <div class="info-card mb-4">
    <h3 class="info-card-title">Search Parameters</h3>

    <div class="config-row">
      <label class="config-label" for="ns-topics">Topics <span class="text-military text-[0.6rem]">*</span></label>
      <input
        id="ns-topics"
        type="text"
        class="config-input config-input-wide"
        bind:value={topics}
        placeholder="e.g. Ukraine, NATO, drones"
      />
    </div>

    <div class="config-row">
      <label class="config-label" for="ns-location">Location</label>
      <input
        id="ns-location"
        type="text"
        class="config-input config-input-wide"
        bind:value={location}
        placeholder="e.g. Ukraine, Middle East"
      />
    </div>

    <div class="config-row">
      <label class="config-label">Date Range</label>
      <div class="flex items-center gap-2">
        <input
          type="date"
          class="config-input"
          style="width: 130px;"
          bind:value={startDate}
        />
        <span class="text-muted text-[0.65rem]">to</span>
        <input
          type="date"
          class="config-input"
          style="width: 130px;"
          bind:value={endDate}
        />
      </div>
    </div>

    <div class="config-row" style="align-items: flex-start;">
      <label class="config-label" for="ns-question" style="margin-top: 6px;">Question</label>
      <textarea
        id="ns-question"
        class="ns-textarea"
        rows="2"
        bind:value={question}
        placeholder="What would you like to know?"
      ></textarea>
    </div>

    <div class="config-row">
      <label class="config-label" for="ns-max">Max Articles</label>
      <div class="flex items-center gap-2">
        <input
          id="ns-max"
          type="range"
          min="5"
          max="50"
          step="5"
          bind:value={maxArticles}
          class="accent-[#78d6ff] w-24"
        />
        <span class="font-mono text-[0.72rem] tabular-nums w-6 text-right">{maxArticles}</span>
      </div>
    </div>
  </div>

  <!-- Action Buttons -->
  <div class="flex gap-3 mb-5">
    <button
      type="button"
      class="admin-btn admin-btn-secondary"
      disabled={loading || !topics.trim()}
      onclick={fetchArticles}
    >
      {#if loading}
        <span class="ns-spinner"></span>
      {:else}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      {/if}
      Fetch Articles
    </button>
    <button
      type="button"
      class="admin-btn"
      disabled={loading || !topics.trim()}
      onclick={fetchAndSummarize}
    >
      {#if loading}
        <span class="ns-spinner"></span>
      {:else}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4zm0 2a2 2 0 0 1 2 2v2H10V6a2 2 0 0 1 2-2zm-3 10a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"/></svg>
      {/if}
      Fetch & Summarize
    </button>
  </div>

  <!-- Loading State -->
  {#if loading}
    <div class="ns-loading">
      <div class="ns-pulse"></div>
      <span class="font-mono text-[0.68rem] text-muted tracking-[0.1em] uppercase">Searching articles...</span>
    </div>
  {/if}

  <!-- Error State -->
  {#if error}
    <div class="ns-error">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
      <span>{error}</span>
    </div>
  {/if}

  <!-- Results -->
  {#if result}
    <!-- Article Count Badge -->
    <div class="flex items-center gap-3 mb-3">
      <span class="font-mono text-[0.65rem] tracking-[0.14em] uppercase text-muted">Results</span>
      <hr class="rule-thin flex-1" />
      <span class="admin-badge">{result.article_count ?? result.articles?.length ?? 0} articles</span>
    </div>

    <!-- Summary Card -->
    {#if result.summary}
      <div class="ns-summary-card mb-4">
        <div class="flex items-center gap-2 mb-2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#78d6ff" stroke-width="1.5"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/></svg>
          <span class="font-mono text-[0.62rem] tracking-[0.14em] uppercase text-blue">AI Summary</span>
        </div>
        <p class="m-0 text-[0.82rem] leading-[1.65] text-body-light">{result.summary}</p>
        {#if result.query}
          <p class="m-0 mt-3 font-mono text-[0.6rem] text-muted tracking-[0.04em]">Query: {result.query}</p>
        {/if}
      </div>
    {/if}

    <!-- Article List -->
    {#if result.articles?.length > 0}
      <div class="ns-article-list">
        {#each result.articles as article, i}
          <div class="ns-article">
            <div class="flex items-start gap-3">
              <span class="ns-article-idx">{i + 1}</span>
              <div class="flex-1 min-w-0">
                <a
                  href={article.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  class="ns-article-title"
                >
                  {article.title}
                </a>
                <div class="flex items-center gap-3 mt-1 mb-1">
                  {#if article.source}
                    <span class="ns-article-source">{article.source}</span>
                  {/if}
                  {#if article.published}
                    <span class="font-mono text-[0.6rem] text-muted">{formatDate(article.published)}</span>
                  {/if}
                </div>
                {#if article.description}
                  <p class="m-0 text-[0.75rem] text-muted leading-[1.55]">{truncate(article.description)}</p>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="ns-empty">
        <span class="font-mono text-[0.68rem] text-muted tracking-[0.06em]">No articles found for the given query.</span>
      </div>
    {/if}
  {/if}
</div>

<style>
  .news-search-panel {
    padding: 20px 0;
  }

  /* ── Connection status dots ── */
  .status-connected {
    background: var(--color-civil);
    box-shadow: 0 0 6px rgba(73, 212, 186, 0.5);
  }
  .status-unreachable {
    background: var(--color-military);
    box-shadow: 0 0 6px rgba(255, 117, 87, 0.5);
  }
  .status-checking {
    background: var(--color-amber);
    animation: ticker-pulse 1.2s infinite;
  }

  /* ── Reuse admin card/row patterns ── */
  .info-card {
    border: 1px solid var(--color-line);
    padding: 16px 20px;
    background: rgba(6, 12, 22, 0.3);
  }
  .info-card-title {
    margin: 0 0 12px;
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-blue);
  }

  .config-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid rgba(138, 166, 196, 0.06);
  }
  .config-row:last-child { border-bottom: none; }

  .config-label {
    font-size: 0.75rem;
    color: var(--color-muted);
  }
  .config-input {
    width: 90px;
    padding: 4px 8px;
    background: rgba(6, 12, 22, 0.5);
    border: 1px solid var(--color-line);
    color: var(--color-text);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    text-align: right;
    outline: none;
    transition: border-color 0.15s;
  }
  .config-input:focus {
    border-color: rgba(120, 214, 255, 0.4);
  }
  .config-input-wide {
    width: 240px;
    text-align: left;
  }

  .ns-textarea {
    width: 240px;
    padding: 8px 10px;
    background: rgba(6, 12, 22, 0.5);
    border: 1px solid var(--color-line);
    color: var(--color-text);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    line-height: 1.5;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
  }
  .ns-textarea::placeholder {
    color: var(--color-muted);
    opacity: 0.5;
  }
  .ns-textarea:focus {
    border-color: rgba(120, 214, 255, 0.4);
  }

  /* ── Buttons (scoped copies) ── */
  .admin-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    background: rgba(120, 214, 255, 0.08);
    border: 1px solid rgba(120, 214, 255, 0.22);
    color: var(--color-blue);
    font-family: var(--font-mono);
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
  }
  .admin-btn:hover:not(:disabled) {
    background: rgba(120, 214, 255, 0.14);
    border-color: rgba(120, 214, 255, 0.36);
  }
  .admin-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }
  .admin-btn-secondary {
    background: rgba(138, 166, 196, 0.06);
    border-color: var(--color-line);
    color: var(--color-body-light);
  }
  .admin-btn-secondary:hover:not(:disabled) {
    background: rgba(138, 166, 196, 0.1);
  }

  .action-btn {
    padding: 4px 10px;
    background: rgba(120, 214, 255, 0.05);
    border: 1px solid rgba(120, 214, 255, 0.15);
    color: var(--color-blue);
    font-family: var(--font-mono);
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.15s;
  }
  .action-btn:hover {
    background: rgba(120, 214, 255, 0.12);
  }

  .admin-badge {
    display: inline-block;
    padding: 2px 8px;
    background: rgba(120, 214, 255, 0.06);
    border: 1px solid rgba(120, 214, 255, 0.14);
    font-family: var(--font-mono);
    font-size: 0.6rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-blue);
  }

  /* ── Loading ── */
  .ns-loading {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px;
    border: 1px solid var(--color-line);
    background: rgba(6, 12, 22, 0.2);
    margin-bottom: 16px;
  }

  .ns-pulse {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--color-blue);
    animation: ticker-pulse 1s ease-in-out infinite;
  }

  .ns-spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(120, 214, 255, 0.2);
    border-top-color: var(--color-blue);
    border-radius: 50%;
    animation: ns-spin 0.6s linear infinite;
  }

  @keyframes ns-spin {
    to { transform: rotate(360deg); }
  }

  /* ── Error ── */
  .ns-error {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border: 1px solid rgba(255, 117, 87, 0.25);
    background: rgba(255, 117, 87, 0.06);
    color: var(--color-military);
    font-size: 0.78rem;
    margin-bottom: 16px;
  }

  /* ── Summary Card ── */
  .ns-summary-card {
    border: 1px solid rgba(120, 214, 255, 0.2);
    background: rgba(120, 214, 255, 0.04);
    padding: 16px 20px;
  }

  /* ── Article List ── */
  .ns-article-list {
    border: 1px solid var(--color-line);
  }

  .ns-article {
    padding: 12px 16px;
    border-bottom: 1px solid var(--color-line);
    transition: background 0.15s;
  }
  .ns-article:last-child {
    border-bottom: none;
  }
  .ns-article:hover {
    background: rgba(120, 214, 255, 0.02);
  }

  .ns-article-idx {
    font-family: var(--font-mono);
    font-size: 0.6rem;
    color: var(--color-muted);
    min-width: 20px;
    padding-top: 2px;
    text-align: right;
  }

  .ns-article-title {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--color-text);
    text-decoration: none;
    line-height: 1.35;
    transition: color 0.15s;
  }
  .ns-article-title:hover {
    color: var(--color-blue);
  }

  .ns-article-source {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--color-blue);
    padding: 1px 6px;
    background: rgba(120, 214, 255, 0.06);
    border: 1px solid rgba(120, 214, 255, 0.12);
  }

  /* ── Empty state ── */
  .ns-empty {
    padding: 32px;
    text-align: center;
    border: 1px dashed var(--color-line);
    background: rgba(6, 12, 22, 0.2);
  }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .config-input-wide {
      width: 160px;
    }
    .ns-textarea {
      width: 160px;
    }
  }
</style>
