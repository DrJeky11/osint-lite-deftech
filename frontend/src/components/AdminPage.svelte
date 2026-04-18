<script>
  import { dataset, scoringConfig, refreshDataset, syncScraperUrl } from "../state.svelte.js";
  import { DEFAULT_SCORING_CONFIG } from "../lib/scoring.js";
  let { onBack = () => {} } = $props();

  let activeTab = $state("sources");

  /* ── Platform definitions ── */
  const platforms = [
    { id: "x", name: "X / Twitter", color: "#f0f4fb", bg: "rgba(240,244,251,0.06)", border: "rgba(240,244,251,0.18)",
      icon: "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z",
      desc: "Posts, threads, and lists" },
    { id: "google", name: "Google News", color: "#78d6ff", bg: "rgba(120,214,255,0.06)", border: "rgba(120,214,255,0.18)",
      icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
      desc: "News search & alerts" },
    { id: "bluesky", name: "Bluesky", color: "#49d4ba", bg: "rgba(73,212,186,0.06)", border: "rgba(73,212,186,0.18)",
      icon: "M12 2C7.31 2 4.5 7.1 3.5 9.5c-1 2.5-.5 6.5 3 7 2.5.3 4-1 5-2.5.2-.3.35-.55.5-.75.15.2.3.45.5.75 1 1.5 2.5 2.8 5 2.5 3.5-.5 4-4.5 3-7C19.5 7.1 16.69 2 12 2z",
      desc: "Posts & feeds" },
    { id: "telegram", name: "Telegram", color: "#78d6ff", bg: "rgba(120,214,255,0.06)", border: "rgba(120,214,255,0.18)",
      icon: "M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z",
      desc: "Channels & groups" },
    { id: "reddit", name: "Reddit", color: "#ff7557", bg: "rgba(255,117,87,0.06)", border: "rgba(255,117,87,0.18)",
      icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5.8 11.33c.02.16.03.33.03.5 0 2.55-2.97 4.62-6.63 4.62s-6.63-2.07-6.63-4.62c0-.17.01-.34.03-.5a1.4 1.4 0 0 1-.53-1.1c0-.78.63-1.4 1.4-1.4.37 0 .7.14.95.38 1.13-.82 2.69-1.35 4.42-1.42l.74-3.49a.3.3 0 0 1 .36-.24l2.47.52a1 1 0 1 1-.1.47l-2.22-.47-.66 3.12c1.72.08 3.26.61 4.38 1.43.25-.24.58-.38.95-.38.78 0 1.4.63 1.4 1.4 0 .44-.2.83-.53 1.1zM9.5 13a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5zm5 0a1.25 1.25 0 1 0 0 2.5 1.25 1.25 0 0 0 0-2.5zm-5.47 3.77c-.08-.08-.08-.22 0-.3.08-.08.22-.08.3 0 .7.7 1.81.88 2.67.88s1.97-.18 2.67-.88c.08-.08.22-.08.3 0 .08.08.08.22 0 .3-.84.84-2.08 1.03-2.97 1.03s-2.13-.19-2.97-1.03z",
      desc: "Subreddits & threads" },
    { id: "rss", name: "RSS Feeds", color: "#ffb25f", bg: "rgba(255,178,95,0.06)", border: "rgba(255,178,95,0.18)",
      icon: "M4 11a9 9 0 0 1 9 9M4 4a16 16 0 0 1 16 16M5 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
      desc: "Custom RSS & Atom feeds" },
    { id: "youtube", name: "YouTube", color: "#ff7557", bg: "rgba(255,117,87,0.06)", border: "rgba(255,117,87,0.18)",
      icon: "M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.1c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33zM9.75 15.02V8.48l5.75 3.27-5.75 3.27z",
      desc: "Channels & live streams" },
    { id: "mastodon", name: "Mastodon", color: "#a78bfa", bg: "rgba(167,139,250,0.06)", border: "rgba(167,139,250,0.18)",
      icon: "M21.26 13.12c-.32 1.63-2.84 3.42-5.74 3.76-1.51.18-3 .34-4.59.27-2.6-.12-4.65-.63-4.65-.63v.71c.34 2.5 2.53 2.65 4.61 2.72 2.1.07 3.97-.52 3.97-.52l.09 1.9s-1.47.79-4.09.93c-1.44.08-3.23-.04-5.32-.56C1.93 20.63 1.1 16.64 1 12.6v-.04c0-4.05.84-7.07 4.54-8.06 2.29-.62 7.67-.88 12.1-.49v.01c.38.04.73.08 1.06.14 2.63.44 4.61 2.14 4.88 3.78.39 2.42.42 5.9-.32 7.7v.01c0-.01 0-.01 0 0zM17.77 7.8c0-1-.26-1.8-.77-2.4-.53-.6-1.23-.9-2.1-.9-1 0-1.76.39-2.26 1.16l-.49.82-.49-.82c-.5-.77-1.25-1.16-2.26-1.16-.87 0-1.57.3-2.1.9-.51.6-.77 1.4-.77 2.4v4.94h1.96V7.95c0-1 .42-1.52 1.27-1.52.94 0 1.41.61 1.41 1.81v2.63h1.95V8.24c0-1.2.47-1.81 1.41-1.81.85 0 1.27.51 1.27 1.52v4.79h1.96V7.8z",
      desc: "Fediverse posts & toots" },
  ];

  /* ── Add-source modal state ── */
  let addingPlatform = $state(null);
  let newSourceLabel = $state("");
  let newSourceUrl = $state("");
  let newSourceKeywords = $state("");

  function openAddSource(platform) {
    addingPlatform = platform;
    newSourceLabel = "";
    newSourceUrl = "";
    newSourceKeywords = "";
  }

  function closeAddSource() {
    addingPlatform = null;
  }

  function submitNewSource() {
    // Placeholder — will wire to backend API
    console.log("Add source:", {
      platform: addingPlatform.id,
      label: newSourceLabel,
      url: newSourceUrl,
      keywords: newSourceKeywords,
    });
    closeAddSource();
  }

  /* ── Count active sources per platform ── */
  function platformSourceCount(platformId) {
    const familyMap = { x: "x", google: "news", bluesky: "bluesky", telegram: "telegram", reddit: "reddit", rss: "news", youtube: "youtube", mastodon: "mastodon" };
    const kindMap = { rss: "rss-feed" };
    const family = familyMap[platformId];
    const kind = kindMap[platformId];
    return sources.filter(s => {
      if (kind) return s.sourceKind === kind;
      if (family) return s.sourceFamily === family || s.id?.includes(platformId);
      return false;
    }).length;
  }

  const tabs = [
    { id: "sources", label: "Data Sources", icon: "M4 4h16v2H4zM4 9h16v2H4zM4 14h10v2H4z" },
    { id: "ai", label: "AI / LLM", icon: "M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4zm0 2a2 2 0 0 1 2 2v2H10V6a2 2 0 0 1 2-2zm-3 10a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm6 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z" },
    { id: "system", label: "System Status", icon: "M22 12h-4l-3 9L9 3l-3 9H2" },
    { id: "config", label: "Configuration", icon: "M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" },
    { id: "logs", label: "Activity Log", icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8" },
    { id: "users", label: "Users & Access", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" },
  ];

  /* ── Scraper Backend Config ── */
  const SCRAPER_STORAGE_KEY = "sa-scraper-config";
  let scraperUrl = $state(localStorage.getItem(SCRAPER_STORAGE_KEY) || "http://localhost:8000");
  let backendStatus = $state("checking"); // "checking" | "online" | "offline"
  let refreshing = $state(false);
  let refreshMessage = $state("");
  let backendSources = $state([]); // live source catalog from backend
  let backendStats = $state({ signals: 0, sources: 0, failures: 0, generatedAt: null });

  function saveScraperUrl() {
    localStorage.setItem(SCRAPER_STORAGE_KEY, scraperUrl);
    syncScraperUrl();
    checkBackend();
  }

  async function checkBackend() {
    backendStatus = "checking";
    try {
      const res = await fetch(scraperUrl + "/health", { signal: AbortSignal.timeout(5000) });
      backendStatus = res.ok ? "online" : "offline";
      if (res.ok) {
        fetchBackendDataset();
        fetchSearches();
        fetchSchedule();
        fetchScoringConfig();
        fetchClassifierConfig();
        fetchCredentials();
      }
    } catch {
      backendStatus = "offline";
    }
  }

  async function fetchBackendDataset() {
    try {
      const res = await fetch(scraperUrl + "/dataset", { signal: AbortSignal.timeout(10000) });
      if (res.ok) {
        const ds = await res.json();
        backendSources = ds.sourceCatalog ?? [];
        backendStats = {
          signals: ds.signalEvents?.length ?? 0,
          sources: ds.sourceCatalog?.length ?? 0,
          failures: ds.failures?.length ?? 0,
          generatedAt: ds.generatedAt ? new Date(ds.generatedAt) : null,
        };
      }
    } catch { /* ignore */ }
  }

  async function refreshAll() {
    refreshing = true;
    refreshMessage = "";
    try {
      const res = await fetch(scraperUrl + "/refresh", {
        method: "POST",
        signal: AbortSignal.timeout(120000),
      });
      if (res.ok) {
        const ds = await res.json();
        // Update local admin state from the full dataset response
        backendSources = ds.sourceCatalog ?? [];
        backendStats = {
          signals: ds.signalEvents?.length ?? 0,
          sources: ds.sourceCatalog?.length ?? 0,
          failures: ds.failures?.length ?? 0,
          generatedAt: ds.generatedAt ? new Date(ds.generatedAt) : null,
        };
        // Push fresh data into the global dataset so the main app sees it
        await refreshDataset(ds);
        refreshMessage = `Refreshed — ${backendStats.signals} signals from ${backendStats.sources} sources`;
      } else {
        refreshMessage = `Refresh failed: HTTP ${res.status}`;
      }
    } catch (e) {
      refreshMessage = `Refresh failed: ${e.message}`;
    }
    refreshing = false;
    setTimeout(() => { refreshMessage = ""; }, 8000);
  }

  let searches = $state([]);
  let schedule = $state({ enabled: false, interval_minutes: 60 });
  let addingMode = $state(null); // null | "group" | "google" | "bluesky" | "x"
  let newLabel = $state("");
  let newTopics = $state("");
  let newLocation = $state("");
  let newPlaceHints = $state("");
  let newMaxArticles = $state(15);
  let expandedGroups = $state(new Set());

  const platformMeta = {
    google: { name: "Google News", color: "#78d6ff", icon: "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" },
    bluesky: { name: "Bluesky", color: "#49d4ba", icon: "M12 2C7.31 2 4.5 7.1 3.5 9.5c-1 2.5-.5 6.5 3 7 2.5.3 4-1 5-2.5.2-.3.35-.55.5-.75.15.2.3.45.5.75 1 1.5 2.5 2.8 5 2.5 3.5-.5 4-4.5 3-7C19.5 7.1 16.69 2 12 2z" },
    x: { name: "X / Twitter", color: "#f0f4fb", icon: "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" },
  };

  /** Group searches by their `group` field for display */
  const searchGroups = $derived.by(() => {
    const groups = new Map();
    for (const s of searches) {
      const g = s.group || s.id;
      if (!groups.has(g)) groups.set(g, { group: g, label: s.label, location: s.location, topics: s.topics, max_articles: s.max_articles, place_hints: s.place_hints, sources: [] });
      groups.get(g).sources.push(s);
    }
    return [...groups.values()];
  });

  function toggleGroup(group) {
    const next = new Set(expandedGroups);
    next.has(group) ? next.delete(group) : next.add(group);
    expandedGroups = next;
  }

  async function fetchSearches() {
    try {
      const res = await fetch(scraperUrl + "/searches", { signal: AbortSignal.timeout(5000) });
      if (res.ok) searches = await res.json();
    } catch {}
  }

  async function fetchSchedule() {
    try {
      const res = await fetch(scraperUrl + "/schedule", { signal: AbortSignal.timeout(5000) });
      if (res.ok) schedule = await res.json();
    } catch {}
  }

  async function saveSchedule() {
    try {
      await fetch(scraperUrl + "/schedule", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(schedule),
      });
    } catch {}
  }

  function resetAddForm() {
    addingMode = null;
    newLabel = ""; newTopics = ""; newLocation = ""; newPlaceHints = ""; newMaxArticles = 15;
  }

  async function addNewSearch() {
    const base = {
      label: newLabel.trim(),
      topics: newTopics.split(",").map(t => t.trim()).filter(Boolean),
      location: newLocation.trim() || null,
      place_hints: newPlaceHints.split(",").map(t => t.trim()).filter(Boolean),
      max_articles: newMaxArticles,
    };
    try {
      let res;
      if (addingMode === "group") {
        // Create sources for ALL platforms
        res = await fetch(scraperUrl + "/searches/group", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(base),
        });
      } else {
        // Create a single platform source
        res = await fetch(scraperUrl + "/searches", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...base, platform: addingMode }),
        });
      }
      if (res.ok) {
        await fetchSearches();
        resetAddForm();
      }
    } catch {}
  }

  async function deleteSearchGroup(group) {
    try {
      await fetch(scraperUrl + "/searches/group/" + encodeURIComponent(group), { method: "DELETE" });
      await fetchSearches();
    } catch {}
  }

  async function deleteSearch(id) {
    try {
      await fetch(scraperUrl + "/searches/" + id, { method: "DELETE" });
      await fetchSearches();
    } catch {}
  }

  /* ── Source Credentials ── */
  let credentials = $state(null);
  let credsSaveMsg = $state("");
  let credsKeyVisible = $state({});
  // Editable credential values (separate from display to avoid overwriting masked values)
  let credsEdit = $state({ bluesky: {}, x: {} });

  async function fetchCredentials() {
    try {
      const res = await fetch(scraperUrl + "/config/credentials", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        credentials = await res.json();
        // Pre-fill non-secret fields for editing
        credsEdit = {
          bluesky: {
            identifier: credentials.bluesky?.identifier || "",
            app_password: "",
            pds_url: credentials.bluesky?.pds_url || "https://bsky.social",
          },
          x: {
            bearer_token: "",
            api_base_url: credentials.x?.api_base_url || "https://api.x.com",
          },
        };
      }
    } catch {}
  }

  async function saveCredentials() {
    // Only send fields that have non-empty values
    const body = {};
    for (const [platform, fields] of Object.entries(credsEdit)) {
      const filtered = {};
      for (const [key, value] of Object.entries(fields)) {
        if (value && value.trim()) filtered[key] = value.trim();
      }
      if (Object.keys(filtered).length) body[platform] = filtered;
    }
    try {
      const res = await fetch(scraperUrl + "/config/credentials", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        credsSaveMsg = "Credentials saved.";
        await fetchCredentials();
        setTimeout(() => { credsSaveMsg = ""; }, 3000);
      }
    } catch (e) {
      credsSaveMsg = `Save failed: ${e.message}`;
    }
  }

  /* ── Scoring Config ── */
  let scoringConfigDirty = $state(false);
  let scoringSaveMsg = $state("");

  async function fetchScoringConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/scoring", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const cfg = await res.json();
        Object.assign(scoringConfig, cfg);
        scoringConfigDirty = false;
      }
    } catch {}
  }

  async function saveScoringConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/scoring", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...scoringConfig }),
      });
      if (res.ok) {
        const cfg = await res.json();
        Object.assign(scoringConfig, cfg);
        scoringConfigDirty = false;
        scoringSaveMsg = "Scoring config saved.";
        setTimeout(() => { scoringSaveMsg = ""; }, 3000);
      }
    } catch (e) {
      scoringSaveMsg = `Save failed: ${e.message}`;
    }
  }

  async function resetScoringConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/scoring/reset", { method: "POST" });
      if (res.ok) {
        const cfg = await res.json();
        Object.assign(scoringConfig, cfg);
        scoringConfigDirty = false;
        scoringSaveMsg = "Reset to defaults.";
        setTimeout(() => { scoringSaveMsg = ""; }, 3000);
      }
    } catch {}
  }

  function updateScoring(key, value) {
    scoringConfig[key] = value;
    scoringConfigDirty = true;
  }

  /* ── Classifier Config ── */
  let classifierConfig = $state(null);
  let classifierDirty = $state(false);
  let classifierSaveMsg = $state("");

  async function fetchClassifierConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/classifier", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        classifierConfig = await res.json();
        classifierDirty = false;
      }
    } catch {}
  }

  async function saveClassifierConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/classifier", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(classifierConfig),
      });
      if (res.ok) {
        classifierConfig = await res.json();
        classifierDirty = false;
        classifierSaveMsg = "Classifier config saved.";
        setTimeout(() => { classifierSaveMsg = ""; }, 3000);
      }
    } catch (e) {
      classifierSaveMsg = `Save failed: ${e.message}`;
    }
  }

  async function resetClassifierConfig() {
    try {
      const res = await fetch(scraperUrl + "/config/classifier/reset", { method: "POST" });
      if (res.ok) {
        classifierConfig = await res.json();
        classifierDirty = false;
        classifierSaveMsg = "Reset to defaults.";
        setTimeout(() => { classifierSaveMsg = ""; }, 3000);
      }
    } catch {}
  }

  function updateClassifierKeywords(key, value) {
    classifierConfig[key] = value.split(",").map(s => s.trim()).filter(Boolean);
    classifierDirty = true;
  }

  // Check backend on mount
  $effect(() => { checkBackend(); });

  /* ── Env-var override warning for AI tab ── */
  let envOverrides = $state(null); // null = not fetched, object = fetched flags

  async function fetchEnvStatus() {
    try {
      const res = await fetch(scraperUrl + "/config/llm/env-status", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        envOverrides = await res.json();
      }
    } catch {
      envOverrides = null; // graceful degradation
    }
  }

  // Fetch env status when AI tab is selected
  $effect(() => {
    if (activeTab === "ai") {
      fetchEnvStatus();
    }
  });

  const envOverrideKeys = $derived.by(() => {
    if (!envOverrides) return [];
    return Object.entries(envOverrides).filter(([, v]) => v).map(([k]) => k);
  });

  /* ── AI / LLM Configuration (persisted to localStorage) ── */
  const AI_STORAGE_KEY = "sa-ai-config";

  function loadAiConfig() {
    try {
      const stored = localStorage.getItem(AI_STORAGE_KEY);
      if (!stored) return defaultAiConfig();
      const parsed = JSON.parse(stored);
      delete parsed.provider; // migrate old configs
      return { ...defaultAiConfig(), ...parsed };
    } catch { return defaultAiConfig(); }
  }

  function defaultAiConfig() {
    return {
      endpoint: "https://api.openai.com/v1",
      apiKey: "",
      model: "gpt-4o",
      temperature: 0.3,
      maxTokens: 4096,
      systemPrompt: "You are an OSINT analyst assistant. Analyze signal events, classify threats, extract geopolitical context, and provide concise intelligence summaries.",
      enableClassification: true,
      enableSummarization: true,
      enableGeoExtraction: true,
      enableTrendAnalysis: false,
      summaryPromptTemplate: "The user requested news on: {request_description}\n\n{question_block}Below are {article_count} article headlines and snippets. Write a concise, factual intelligence summary of the key events, organized by theme or chronology, and call out notable trends or disagreements between sources. Do not invent facts beyond what's in the snippets.\n\nARTICLES:\n{articles}",
      rateLimitRpm: 60,
      timeoutMs: 30000,
    };
  }

  let aiConfig = $state(loadAiConfig());
  let aiTestStatus = $state(null); // null | "testing" | "success" | "error"
  let aiTestMessage = $state("");
  let aiKeyVisible = $state(false);

  async function saveAiConfig() {
    localStorage.setItem(AI_STORAGE_KEY, JSON.stringify(aiConfig));
    // Also persist feature toggles and system prompt to backend
    try {
      await fetch(scraperUrl + "/config/llm", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          endpoint: aiConfig.endpoint,
          model: aiConfig.model,
          temperature: aiConfig.temperature,
          maxTokens: aiConfig.maxTokens,
          apiKey: aiConfig.apiKey,
          enableClassification: aiConfig.enableClassification,
          enableSummarization: aiConfig.enableSummarization,
          enableGeoExtraction: aiConfig.enableGeoExtraction,
          enableTrendAnalysis: aiConfig.enableTrendAnalysis,
          systemPrompt: aiConfig.systemPrompt,
          rateLimitRpm: aiConfig.rateLimitRpm,
          timeoutMs: aiConfig.timeoutMs,
        }),
      });
    } catch { /* backend save is best-effort */ }
    aiTestStatus = "success";
    aiTestMessage = "Configuration saved.";
    setTimeout(() => { aiTestStatus = null; aiTestMessage = ""; }, 3000);
  }

  async function loadAiConfigFromBackend() {
    try {
      const res = await fetch(scraperUrl + "/config/llm", { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const backendCfg = await res.json();
        // Backend is source of truth for feature toggles and system prompt
        if (backendCfg.enableClassification !== undefined) aiConfig.enableClassification = backendCfg.enableClassification;
        if (backendCfg.enableSummarization !== undefined) aiConfig.enableSummarization = backendCfg.enableSummarization;
        if (backendCfg.enableGeoExtraction !== undefined) aiConfig.enableGeoExtraction = backendCfg.enableGeoExtraction;
        if (backendCfg.enableTrendAnalysis !== undefined) aiConfig.enableTrendAnalysis = backendCfg.enableTrendAnalysis;
        if (backendCfg.systemPrompt) aiConfig.systemPrompt = backendCfg.systemPrompt;
        if (backendCfg.endpoint) aiConfig.endpoint = backendCfg.endpoint;
        if (backendCfg.model) aiConfig.model = backendCfg.model;
        if (backendCfg.temperature !== undefined) aiConfig.temperature = backendCfg.temperature;
        if (backendCfg.maxTokens !== undefined) aiConfig.maxTokens = backendCfg.maxTokens;
      }
    } catch { /* ignore — local config is fallback */ }
  }

  // Load backend AI config when AI tab is selected
  $effect(() => {
    if (activeTab === "ai") {
      loadAiConfigFromBackend();
    }
  });

  function resetAiConfig() {
    aiConfig = defaultAiConfig();
    localStorage.removeItem(AI_STORAGE_KEY);
  }

  async function testAiConnection() {
    aiTestStatus = "testing";
    aiTestMessage = "Testing connection...";
    try {
      const res = await fetch(aiConfig.endpoint + "/models", {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${aiConfig.apiKey}`,
          "Content-Type": "application/json",
        },
        signal: AbortSignal.timeout(aiConfig.timeoutMs),
      });
      if (res.ok) {
        aiTestStatus = "success";
        aiTestMessage = `Connected — ${(await res.json()).data?.length ?? "?"} models available`;
      } else {
        aiTestStatus = "error";
        aiTestMessage = `HTTP ${res.status}: ${res.statusText}`;
      }
    } catch (e) {
      aiTestStatus = "error";
      aiTestMessage = e.name === "TimeoutError" ? "Connection timed out" : e.message;
    }
  }

  /* ── Source status helpers ── */
  const sources = $derived(dataset.sourceCatalog ?? []);
  const failures = $derived(dataset.failures ?? []);
  const generatedAt = $derived(dataset.generatedAt ? new Date(dataset.generatedAt) : null);
  const totalItems = $derived(sources.reduce((sum, s) => sum + (s.itemCount ?? 0), 0));

  function sourceStatus(src) {
    const failed = failures.some(f => f.id === src.id || f.sourceId === src.id);
    return failed ? "error" : src.itemCount > 0 ? "healthy" : "empty";
  }

  function timeAgo(date) {
    if (!date) return "unknown";
    const mins = Math.round((Date.now() - date.getTime()) / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.round(mins / 60);
    return `${hrs}h ago`;
  }
</script>

<div class="w-[min(1560px,calc(100vw-32px))] mx-auto py-5 pb-8 animate-[shell-in_720ms_ease_both]">

  <!-- Admin Header -->
  <div class="flex items-center gap-4 mb-4">
    <h1 class="m-0 text-xl font-semibold tracking-tight">Administration</h1>
    <span class="font-mono text-[0.6rem] tracking-[0.14em] uppercase text-muted px-2 py-1 border border-line">v0.1.0</span>
  </div>
  <hr class="rule-heavy mb-5" />

  <!-- Tab Navigation -->
  <div class="admin-layout">
    <aside class="admin-sidebar">
      {#each tabs as tab}
        <button
          type="button"
          class="admin-tab"
          class:admin-tab-active={activeTab === tab.id}
          onclick={() => activeTab = tab.id}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d={tab.icon} />
          </svg>
          {tab.label}
        </button>
      {/each}
    </aside>

    <main class="admin-content">

      <!-- ═══════ DATA SOURCES ═══════ -->
      {#if activeTab === "sources"}
        <div class="admin-section">
          <h2 class="admin-heading">Data Sources</h2>
          <p class="admin-desc">Sources are configured and scraped by the backend. Connect the backend to view active sources and trigger refreshes.</p>

          <!-- ── Backend Connection ── -->
          <div class="info-card mb-4">
            <h3 class="info-card-title">Scraper Backend</h3>
            <div class="config-row">
              <label class="config-label">Backend URL</label>
              <div class="flex items-center gap-2">
                <input type="text" class="config-input config-input-wide" bind:value={scraperUrl} placeholder="http://localhost:8000" />
                <button type="button" class="action-btn" onclick={saveScraperUrl}>Save</button>
              </div>
            </div>
            <div class="config-row">
              <label class="config-label">Status</label>
              <div class="flex items-center gap-2">
                <span class="status-dot" class:status-healthy={backendStatus === 'online'} class:status-error={backendStatus === 'offline'} style={backendStatus === 'checking' ? 'background: #ffb25f; box-shadow: 0 0 6px rgba(255,178,95,0.4);' : ''}></span>
                <span class="text-[0.72rem] capitalize">{backendStatus}</span>
                {#if backendStatus === 'offline'}
                  <span class="font-mono text-[0.6rem] text-muted">— run: uvicorn main:app --reload</span>
                {/if}
              </div>
            </div>
          </div>

          <!-- ── Source Credentials ── -->
          <div class="info-card mb-4">
            <h3 class="info-card-title">Source Credentials</h3>
            <p class="m-0 mb-3 text-[0.68rem] text-muted">Configure API credentials for each data source. Google News requires no credentials.</p>

            {#if credentials}
            <div class="grid grid-cols-2 gap-4 max-[820px]:grid-cols-1">
              <!-- Bluesky -->
              <div style="border: 1px solid rgba(73,212,186,0.15); border-radius: 6px; padding: 12px;">
                <div class="flex items-center gap-2 mb-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="#49d4ba"><path d={platformMeta.bluesky.icon} /></svg>
                  <span class="text-[0.78rem] font-medium" style="color: #49d4ba;">Bluesky</span>
                  {#if credentials.bluesky?.app_password_set}
                    <span class="text-[0.6rem] px-1.5 py-0.5 rounded" style="background: rgba(73,212,186,0.12); color: #49d4ba;">configured</span>
                  {:else}
                    <span class="text-[0.6rem] px-1.5 py-0.5 rounded" style="background: rgba(255,117,87,0.12); color: #ff7557;">not set</span>
                  {/if}
                </div>
                <div class="config-row">
                  <label class="config-label">Identifier</label>
                  <input type="text" class="config-input config-input-wide" bind:value={credsEdit.bluesky.identifier} placeholder="your-handle.bsky.social" />
                </div>
                <div class="config-row">
                  <label class="config-label">App Password</label>
                  <div class="flex items-center gap-1">
                    <input
                      type={credsKeyVisible.bluesky ? "text" : "password"}
                      class="config-input config-input-wide"
                      bind:value={credsEdit.bluesky.app_password}
                      placeholder={credentials.bluesky?.app_password_set ? "(saved — leave blank to keep)" : "xxxx-xxxx-xxxx-xxxx"}
                    />
                    <button type="button" class="action-btn" style="padding: 5px 6px; min-width: unset;" onclick={() => credsKeyVisible = {...credsKeyVisible, bluesky: !credsKeyVisible.bluesky}}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        {#if credsKeyVisible.bluesky}
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22"/>
                        {:else}
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                        {/if}
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="config-row">
                  <label class="config-label">PDS URL</label>
                  <input type="text" class="config-input config-input-wide" bind:value={credsEdit.bluesky.pds_url} placeholder="https://bsky.social" />
                </div>
              </div>

              <!-- X / Twitter -->
              <div style="border: 1px solid rgba(240,244,251,0.15); border-radius: 6px; padding: 12px;">
                <div class="flex items-center gap-2 mb-2">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="#f0f4fb"><path d={platformMeta.x.icon} /></svg>
                  <span class="text-[0.78rem] font-medium" style="color: #f0f4fb;">X / Twitter</span>
                  {#if credentials.x?.bearer_token_set}
                    <span class="text-[0.6rem] px-1.5 py-0.5 rounded" style="background: rgba(240,244,251,0.12); color: #f0f4fb;">configured</span>
                  {:else}
                    <span class="text-[0.6rem] px-1.5 py-0.5 rounded" style="background: rgba(255,117,87,0.12); color: #ff7557;">not set</span>
                  {/if}
                </div>
                <div class="config-row">
                  <label class="config-label">Bearer Token</label>
                  <div class="flex items-center gap-1">
                    <input
                      type={credsKeyVisible.x ? "text" : "password"}
                      class="config-input config-input-wide"
                      bind:value={credsEdit.x.bearer_token}
                      placeholder={credentials.x?.bearer_token_set ? "(saved — leave blank to keep)" : "AAAA..."}
                    />
                    <button type="button" class="action-btn" style="padding: 5px 6px; min-width: unset;" onclick={() => credsKeyVisible = {...credsKeyVisible, x: !credsKeyVisible.x}}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        {#if credsKeyVisible.x}
                          <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22"/>
                        {:else}
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                        {/if}
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="config-row">
                  <label class="config-label">API Base URL</label>
                  <input type="text" class="config-input config-input-wide" bind:value={credsEdit.x.api_base_url} placeholder="https://api.x.com" />
                </div>
              </div>
            </div>

            <div class="mt-3 flex items-center gap-3">
              <button type="button" class="admin-btn" onclick={saveCredentials} disabled={backendStatus !== 'online'}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                Save Credentials
              </button>
              {#if credsSaveMsg}
                <span class="font-mono text-[0.65rem]" class:text-civil={!credsSaveMsg.includes('failed')} class:text-military={credsSaveMsg.includes('failed')}>{credsSaveMsg}</span>
              {/if}
            </div>
            {:else if backendStatus === 'online'}
              <p class="text-[0.72rem] text-muted">Loading credentials...</p>
            {:else}
              <p class="text-[0.72rem] text-muted">Connect backend to configure credentials.</p>
            {/if}
          </div>

          <!-- ── Stats Ribbon (from backend) ── -->
          <div class="grid grid-cols-4 gap-px bg-line mb-5 max-[820px]:grid-cols-2">
            <div class="stat-cell bg-bg">
              <span class="stat-label">Total Sources</span>
              <strong class="stat-value">{backendSources.length || sources.length}</strong>
            </div>
            <div class="stat-cell bg-bg">
              <span class="stat-label">Signal Events</span>
              <strong class="stat-value">{backendStats.signals || totalItems}</strong>
            </div>
            <div class="stat-cell bg-bg">
              <span class="stat-label">Last Refresh</span>
              <strong class="stat-value text-[1rem]">{backendStats.generatedAt ? timeAgo(backendStats.generatedAt) : timeAgo(generatedAt)}</strong>
            </div>
            <div class="stat-cell bg-bg">
              <span class="stat-label">Failures</span>
              <strong class="stat-value" class:text-military={backendStats.failures > 0}>{backendStats.failures || failures.length}</strong>
            </div>
          </div>

          <!-- ── Refresh Schedule ── -->
          <div class="info-card mb-4">
            <h3 class="info-card-title">Refresh Schedule</h3>
            <div class="config-row">
              <label class="config-label">Auto-refresh</label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" bind:checked={schedule.enabled} onchange={saveSchedule} class="w-4 h-4 accent-[var(--color-blue)] cursor-pointer" />
                <span class="text-[0.72rem]">{schedule.enabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if schedule.enabled}
            <div class="config-row">
              <label class="config-label">Interval</label>
              <select class="config-input" bind:value={schedule.interval_minutes} onchange={saveSchedule}>
                <option value={15}>Every 15 min</option>
                <option value={30}>Every 30 min</option>
                <option value={60}>Every hour</option>
                <option value={120}>Every 2 hours</option>
                <option value={360}>Every 6 hours</option>
                <option value={720}>Every 12 hours</option>
                <option value={1440}>Every 24 hours</option>
              </select>
            </div>
            {/if}
          </div>

          <!-- ── Configured Searches ── -->
          <div class="flex items-center gap-3 mb-3 flex-wrap">
            <span class="font-mono text-[0.65rem] tracking-[0.14em] uppercase text-muted">Configured Searches</span>
            <hr class="rule-thin flex-1" />
            {#if addingMode}
              <button type="button" class="admin-btn" style="padding: 6px 14px;" onclick={resetAddForm}>✕ Cancel</button>
            {:else}
              <button type="button" class="admin-btn" style="padding: 6px 14px;" onclick={() => addingMode = 'group'} disabled={backendStatus !== 'online'}>+ Search All</button>
              {#each Object.entries(platformMeta) as [pid, plat]}
                <button type="button" class="admin-btn" style="padding: 6px 14px; border-color: {plat.color}33; color: {plat.color};" onclick={() => addingMode = pid} disabled={backendStatus !== 'online'}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" opacity="0.7"><path d={plat.icon} /></svg>
                  + {plat.name}
                </button>
              {/each}
            {/if}
          </div>

          {#if addingMode}
          {@const isGroup = addingMode === 'group'}
          {@const formMeta = isGroup ? { name: 'All Platforms', color: '#f0f4fb' } : platformMeta[addingMode]}
          <div class="info-card mb-4" style="border-color: {formMeta.color}22;">
            <h3 class="info-card-title" style="color: {formMeta.color};">
              {isGroup ? 'New Search (All Platforms)' : `New ${formMeta.name} Source`}
            </h3>
            <p class="m-0 mb-3 text-[0.68rem] text-muted">
              {isGroup
                ? 'Creates sources for all platforms (Google News, Bluesky, X) sharing the same keywords and location.'
                : `Creates a single ${formMeta.name} source with the specified keywords.`}
            </p>
            <div class="grid gap-2">
              <div class="config-row"><label class="config-label">Label</label><input type="text" class="config-input config-input-wide" bind:value={newLabel} placeholder="e.g. Sudan Conflict" /></div>
              <div class="config-row"><label class="config-label">Topics (comma-sep)</label><input type="text" class="config-input config-input-wide" bind:value={newTopics} placeholder="e.g. Sudan conflict, RSF Khartoum" /></div>
              <div class="config-row"><label class="config-label">Location</label><input type="text" class="config-input config-input-wide" bind:value={newLocation} placeholder="e.g. Sudan (optional)" /></div>
              <div class="config-row"><label class="config-label">Place Hints (comma-sep)</label><input type="text" class="config-input config-input-wide" bind:value={newPlaceHints} placeholder="e.g. Sudan, Khartoum" /></div>
              <div class="config-row"><label class="config-label">Max Results</label><input type="number" class="config-input" bind:value={newMaxArticles} min="5" max="50" /></div>
            </div>
            <div class="mt-3">
              <button type="button" class="admin-btn" style="border-color: {formMeta.color}44; color: {formMeta.color};" onclick={addNewSearch} disabled={!newLabel.trim() || !newTopics.trim()}>
                {isGroup ? 'Create Search Group' : `Add ${formMeta.name} Source`}
              </button>
            </div>
          </div>
          {/if}

          <div class="admin-table-wrap mb-5">
            <table class="admin-table">
              <thead><tr><th style="width: 28%;">Search</th><th>Sources</th><th>Topics</th><th>Location</th><th>Max</th><th></th></tr></thead>
              <tbody>
                {#each searchGroups as grp}
                  {@const isExpanded = expandedGroups.has(grp.group)}
                  <!-- Group header row -->
                  <tr class="cursor-pointer" style="border-left: 3px solid rgba(240,244,251,0.15);" onclick={() => toggleGroup(grp.group)}>
                    <td>
                      <div class="flex items-center gap-2">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transition: transform 150ms; transform: rotate({isExpanded ? 90 : 0}deg); opacity: 0.4;">
                          <path d="M9 18l6-6-6-6" />
                        </svg>
                        <div class="flex flex-col">
                          <span class="font-medium text-[0.82rem]">{grp.label}</span>
                          <span class="font-mono text-[0.58rem] text-muted">{grp.group}</span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div class="flex items-center gap-1.5">
                        {#each grp.sources as src}
                          {@const plat = platformMeta[src.platform] || platformMeta.google}
                          <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.62rem] font-medium" style="background: {plat.color}12; color: {plat.color}; border: 1px solid {plat.color}22;" title={src.id}>
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d={plat.icon} /></svg>
                            {plat.name}
                          </span>
                        {/each}
                      </div>
                    </td>
                    <td class="font-mono text-[0.68rem] text-muted">{(grp.topics || []).join(", ")}</td>
                    <td class="text-[0.72rem]">{grp.location || "—"}</td>
                    <td class="tabular-nums">{grp.max_articles}</td>
                    <td>
                      <button type="button" class="action-btn action-danger" onclick={(e) => { e.stopPropagation(); deleteSearchGroup(grp.group); }} title="Delete entire search group">Delete</button>
                    </td>
                  </tr>
                  <!-- Expanded sub-sources -->
                  {#if isExpanded}
                    {#each grp.sources as src}
                      {@const plat = platformMeta[src.platform] || platformMeta.google}
                      <tr style="background: rgba(240,244,251,0.02); border-left: 3px solid {plat.color}33;">
                        <td class="pl-8">
                          <div class="flex items-center gap-2">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill={plat.color}><path d={plat.icon} /></svg>
                            <span class="text-[0.76rem]" style="color: {plat.color};">{plat.name}</span>
                          </div>
                          <span class="font-mono text-[0.58rem] text-muted pl-5">{src.id}</span>
                        </td>
                        <td><span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[0.62rem] font-medium" style="background: {plat.color}12; color: {plat.color}; border: 1px solid {plat.color}22;">{plat.name}</span></td>
                        <td class="font-mono text-[0.68rem] text-muted">{(src.topics || []).join(", ")}</td>
                        <td class="text-[0.72rem]">{src.location || "—"}</td>
                        <td class="tabular-nums">{src.max_articles}</td>
                        <td><button type="button" class="action-btn action-danger" onclick={() => deleteSearch(src.id)} title="Remove this platform source only">Remove</button></td>
                      </tr>
                    {/each}
                  {/if}
                {/each}
                {#if searchGroups.length === 0}
                  <tr><td colspan="6" class="text-center text-muted font-mono text-[0.72rem] py-6">{backendStatus === 'online' ? 'No searches configured' : 'Connect backend to manage'}</td></tr>
                {/if}
              </tbody>
            </table>
          </div>

          <!-- ── Refresh Controls ── -->
          <div class="flex items-center gap-3 mb-3">
            <span class="font-mono text-[0.65rem] tracking-[0.14em] uppercase text-muted">Active Sources</span>
            <hr class="rule-thin flex-1" />
            {#if refreshMessage}
              <span class="font-mono text-[0.6rem]" class:text-civil={!refreshMessage.includes('failed')} class:text-military={refreshMessage.includes('failed')}>{refreshMessage}</span>
            {/if}
            <button
              type="button"
              class="admin-btn"
              style="padding: 6px 14px;"
              disabled={backendStatus !== 'online' || refreshing}
              onclick={refreshAll}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class:animate-spin={refreshing}><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              {refreshing ? 'Refreshing...' : 'Refresh All'}
            </button>
          </div>

          <!-- ── Sources Table (prefers backend data, falls back to static dataset) ── -->
          {#if true}
          {@const displaySources = backendSources.length ? backendSources : sources}
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Family</th>
                  <th>Type</th>
                  <th>Items</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {#each displaySources as src}
                  {@const status = sourceStatus(src)}
                  <tr>
                    <td>
                      <div class="flex flex-col">
                        <span class="font-medium text-[0.82rem]">{src.label}</span>
                        <span class="font-mono text-[0.6rem] text-muted truncate max-w-[240px]">{src.id}</span>
                      </div>
                    </td>
                    <td><span class="admin-badge">{src.sourceFamily}</span></td>
                    <td class="font-mono text-[0.68rem] text-muted">{src.sourceKind ?? "—"}</td>
                    <td class="tabular-nums">{src.itemCount ?? 0}</td>
                    <td>
                      <span class="status-dot status-{status}"></span>
                      <span class="text-[0.72rem] capitalize">{status}</span>
                    </td>
                  </tr>
                {/each}
                {#if displaySources.length === 0}
                  <tr>
                    <td colspan="5" class="text-center text-muted font-mono text-[0.72rem] py-8">
                      {backendStatus === 'online' ? 'No sources yet — click Refresh All to fetch data' : 'Connect the backend to see sources'}
                    </td>
                  </tr>
                {/if}
              </tbody>
            </table>
          </div>
          {/if}
        </div>

      <!-- ═══════ AI / LLM ═══════ -->
      {:else if activeTab === "ai"}
        <div class="admin-section">
          <h2 class="admin-heading">AI / LLM Configuration</h2>
          <p class="admin-desc">Connect any OpenAI-compatible endpoint for signal classification, summarization, and threat analysis.</p>

          {#if envOverrideKeys.length > 0}
            <div class="env-warning-banner">
              <span class="env-warning-icon">&#9888;</span>
              <span>Environment variables detected (<strong>{envOverrideKeys.join(", ")}</strong>) that may override settings configured here. Contact your system administrator to update the deployment configuration.</span>
            </div>
          {/if}

          <div class="grid grid-cols-2 gap-4 max-[820px]:grid-cols-1">
            <!-- Endpoint & Auth -->
            <div class="info-card">
              <h3 class="info-card-title">Endpoint & Authentication</h3>
              <p class="m-0 mb-3 text-[0.68rem] text-muted">Any OpenAI-compatible API — OpenAI, Anthropic, Azure, Ollama, LiteLLM, vLLM, etc.</p>
              <div class="config-row">
                <label class="config-label">Base URL</label>
                <input type="text" class="config-input config-input-wide" bind:value={aiConfig.endpoint} placeholder="https://api.openai.com/v1" />
              </div>
              <div class="config-row">
                <label class="config-label">API Key</label>
                <div class="flex items-center gap-1">
                  <input
                    type={aiKeyVisible ? "text" : "password"}
                    class="config-input config-input-wide"
                    bind:value={aiConfig.apiKey}
                    placeholder="sk-... or leave blank for local"
                  />
                  <button
                    type="button"
                    class="action-btn"
                    style="padding: 5px 6px; min-width: unset;"
                    onclick={() => aiKeyVisible = !aiKeyVisible}
                    title={aiKeyVisible ? "Hide" : "Show"}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      {#if aiKeyVisible}
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19M1 1l22 22"/>
                      {:else}
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                      {/if}
                    </svg>
                  </button>
                </div>
              </div>
              <div class="mt-3 flex items-center gap-3">
                <button type="button" class="admin-btn" onclick={testAiConnection} disabled={aiTestStatus === "testing"}>
                  {#if aiTestStatus === "testing"}
                    Testing...
                  {:else}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
                    Test Connection
                  {/if}
                </button>
                {#if aiTestStatus === "success"}
                  <span class="font-mono text-[0.65rem] text-[#49d4ba]">{aiTestMessage}</span>
                {:else if aiTestStatus === "error"}
                  <span class="font-mono text-[0.65rem] text-[#ff7557]">{aiTestMessage}</span>
                {/if}
              </div>
            </div>

            <!-- Model & Parameters -->
            <div class="info-card">
              <h3 class="info-card-title">Model & Parameters</h3>
              <div class="config-row">
                <label class="config-label">Model</label>
                <input type="text" class="config-input config-input-wide" bind:value={aiConfig.model} placeholder="gpt-4o, claude-sonnet-4-20250514, llama3, etc." />
              </div>
              <div class="config-row">
                <label class="config-label">Temperature</label>
                <div class="flex items-center gap-2">
                  <input type="range" min="0" max="100" value={aiConfig.temperature * 100} oninput={(e) => aiConfig.temperature = Number(e.target.value) / 100} class="accent-[#78d6ff] w-20" />
                  <span class="font-mono text-[0.68rem] tabular-nums w-8 text-right">{aiConfig.temperature.toFixed(2)}</span>
                </div>
              </div>
              <div class="config-row">
                <label class="config-label">Max Tokens</label>
                <input type="number" class="config-input" bind:value={aiConfig.maxTokens} min="256" max="128000" step="256" />
              </div>
              <div class="config-row">
                <label class="config-label">Rate Limit (req/min)</label>
                <input type="number" class="config-input" bind:value={aiConfig.rateLimitRpm} min="1" max="10000" />
              </div>
              <div class="config-row">
                <label class="config-label">Timeout (ms)</label>
                <input type="number" class="config-input" bind:value={aiConfig.timeoutMs} min="5000" max="120000" step="1000" />
              </div>
            </div>

            <!-- System Prompt -->
            <div class="info-card" style="grid-column: 1 / -1;">
              <h3 class="info-card-title">System Prompt</h3>
              <textarea
                class="config-textarea"
                rows="4"
                bind:value={aiConfig.systemPrompt}
                placeholder="System prompt for the AI analyst..."
              ></textarea>
            </div>

            <!-- Summary Prompt Template -->
            <div class="info-card" style="grid-column: 1 / -1;">
              <h3 class="info-card-title">Summary Prompt Template</h3>
              <p class="m-0 mb-2 text-[0.65rem] text-muted">
                Template for article summarization. Available variables: {'{request_description}'}, {'{question_block}'}, {'{article_count}'}, {'{articles}'}
              </p>
              <textarea
                class="config-textarea"
                rows="6"
                bind:value={aiConfig.summaryPromptTemplate}
                placeholder="Below are {'{article_count}'} articles..."
              ></textarea>
            </div>

            <!-- AI Features -->
            <div class="info-card">
              <h3 class="info-card-title">AI Features</h3>
              <label class="ai-toggle">
                <input type="checkbox" bind:checked={aiConfig.enableClassification} />
                <div>
                  <span class="ai-toggle-label">Signal Classification</span>
                  <span class="ai-toggle-desc">Classify events as civil, military, or hybrid</span>
                </div>
              </label>
              <label class="ai-toggle">
                <input type="checkbox" bind:checked={aiConfig.enableSummarization} />
                <div>
                  <span class="ai-toggle-label">Intelligence Summarization</span>
                  <span class="ai-toggle-desc">Generate theater briefs and evidence summaries</span>
                </div>
              </label>
              <label class="ai-toggle">
                <input type="checkbox" bind:checked={aiConfig.enableGeoExtraction} />
                <div>
                  <span class="ai-toggle-label">Geo-Entity Extraction</span>
                  <span class="ai-toggle-desc">Extract locations, organizations, and actors from text</span>
                </div>
              </label>
              <label class="ai-toggle">
                <input type="checkbox" bind:checked={aiConfig.enableTrendAnalysis} />
                <div>
                  <span class="ai-toggle-label">Trend Analysis</span>
                  <span class="ai-toggle-desc">Predict escalation/de-escalation trajectories</span>
                </div>
              </label>
            </div>

            <!-- Current Config Summary -->
            <div class="info-card">
              <h3 class="info-card-title">Current Configuration</h3>
              <div class="info-row"><span>Endpoint</span><span class="font-mono text-[0.65rem] truncate max-w-[200px]" title={aiConfig.endpoint}>{aiConfig.endpoint}</span></div>
              <div class="info-row"><span>Model</span><span class="font-mono text-[0.7rem]">{aiConfig.model}</span></div>
              <div class="info-row"><span>Features Active</span><span>{[aiConfig.enableClassification, aiConfig.enableSummarization, aiConfig.enableGeoExtraction, aiConfig.enableTrendAnalysis].filter(Boolean).length} / 4</span></div>
              <div class="info-row">
                <span>API Key</span>
                <span class="font-mono text-[0.65rem]">
                  {#if aiConfig.apiKey}
                    {aiConfig.apiKey.slice(0, 6)}...{aiConfig.apiKey.slice(-4)}
                  {:else}
                    <span class="text-muted">Not set</span>
                  {/if}
                </span>
              </div>
            </div>
          </div>

          <div class="mt-4 flex gap-3">
            <button type="button" class="admin-btn" onclick={saveAiConfig}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              Save Configuration
            </button>
            <button type="button" class="admin-btn admin-btn-secondary" onclick={resetAiConfig}>
              Reset to Defaults
            </button>
          </div>
        </div>

      <!-- ═══════ SYSTEM STATUS ═══════ -->
      {:else if activeTab === "system"}
        <div class="admin-section">
          <h2 class="admin-heading">System Status</h2>
          <p class="admin-desc">Monitor application health, data pipeline status, and resource usage.</p>

          <div class="grid grid-cols-3 gap-px bg-line mb-5 max-[820px]:grid-cols-1">
            <div class="stat-cell bg-bg">
              <span class="stat-label">App Status</span>
              <div class="flex items-center gap-2">
                <span class="status-dot status-healthy"></span>
                <strong class="text-civil text-sm">Operational</strong>
              </div>
            </div>
            <div class="stat-cell bg-bg">
              <span class="stat-label">Data Pipeline</span>
              <div class="flex items-center gap-2">
                <span class="status-dot status-healthy"></span>
                <strong class="text-civil text-sm">Running</strong>
              </div>
            </div>
            <div class="stat-cell bg-bg">
              <span class="stat-label">Last Build</span>
              <strong class="stat-value text-[1rem]">{generatedAt?.toLocaleString() ?? "—"}</strong>
            </div>
          </div>

          <!-- System info cards -->
          <div class="grid grid-cols-2 gap-4 max-[820px]:grid-cols-1">
            <div class="info-card">
              <h3 class="info-card-title">Data Pipeline</h3>
              <div class="info-row"><span>Signal Events</span><span class="tabular-nums">{dataset.signalEvents?.length ?? 0}</span></div>
              <div class="info-row"><span>Source Catalog</span><span class="tabular-nums">{sources.length} feeds</span></div>
              <div class="info-row"><span>Generation Time</span><span>{generatedAt?.toISOString().slice(0,19) ?? "—"}</span></div>
              <div class="info-row"><span>Failed Feeds</span><span class:text-military={failures.length > 0}>{failures.length}</span></div>
            </div>
            <div class="info-card">
              <h3 class="info-card-title">Frontend</h3>
              <div class="info-row"><span>Framework</span><span>Svelte 5</span></div>
              <div class="info-row"><span>Map Engine</span><span>MapLibre GL</span></div>
              <div class="info-row"><span>Build Tool</span><span>Vite</span></div>
              <div class="info-row"><span>Styling</span><span>Tailwind CSS 4</span></div>
            </div>
          </div>
        </div>

      <!-- ═══════ CONFIGURATION ═══════ -->
      {:else if activeTab === "config"}
        <div class="admin-section">
          <h2 class="admin-heading">Configuration</h2>
          <p class="admin-desc">Adjust scoring parameters, classifier keywords, and display preferences. Changes take effect on the next data refresh.</p>

          <div class="grid grid-cols-2 gap-4 max-[820px]:grid-cols-1">
            <!-- Scoring Model -->
            <div class="info-card">
              <h3 class="info-card-title">Scoring Model</h3>
              <div class="config-row">
                <label class="config-label">Recency Decay (hours)</label>
                <input type="number" class="config-input" value={scoringConfig.recencyDecayHours} step="1" min="1" max="72" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('recencyDecayHours', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Corroboration Boost</label>
                <input type="number" class="config-input" value={scoringConfig.corroborationBoost} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('corroborationBoost', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Civil Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.civilMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('civilMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Military Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.militaryMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('militaryMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">War Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.warMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('warMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Terrorism Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.terrorismMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('terrorismMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Humanitarian Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.humanitarianMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('humanitarianMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Infowar Multiplier</label>
                <input type="number" class="config-input" value={scoringConfig.infowarMultiplier} step="0.1" min="0" max="20" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('infowarMultiplier', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">War Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.war ?? 0.25} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.war = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Military Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.military ?? 0.20} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.military = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Civil Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.civil ?? 0.18} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.civil = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Terrorism Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.terrorism ?? 0.15} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.terrorism = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Humanitarian Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.humanitarian ?? 0.12} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.humanitarian = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Infowar Blend Weight</label>
                <input type="number" class="config-input" value={scoringConfig.blendWeights?.infowar ?? 0.10} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => { if (!scoringConfig.blendWeights) scoringConfig.blendWeights = {}; scoringConfig.blendWeights.infowar = Number(e.target.value); scoringConfigDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Single-Source Penalty</label>
                <input type="number" class="config-input" value={scoringConfig.singleSourcePenalty} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('singleSourcePenalty', Number(e.target.value))} />
              </div>
            </div>

            <!-- Thresholds & Confidence -->
            <div class="info-card">
              <h3 class="info-card-title">Thresholds & Confidence</h3>
              <div class="config-row">
                <label class="config-label">Warming Delta Threshold</label>
                <input type="number" class="config-input" value={scoringConfig.warmingThreshold} step="1" min="1" max="50" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('warmingThreshold', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Cooling Delta Threshold</label>
                <input type="number" class="config-input" value={scoringConfig.coolingThreshold} step="1" min="-50" max="0" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('coolingThreshold', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Confidence Floor</label>
                <input type="number" class="config-input" value={scoringConfig.confidenceFloor} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('confidenceFloor', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Confidence Ceiling</label>
                <input type="number" class="config-input" value={scoringConfig.confidenceCeiling} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('confidenceCeiling', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Confidence Base Weight</label>
                <input type="number" class="config-input" value={scoringConfig.confidenceBaseWeight} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('confidenceBaseWeight', Number(e.target.value))} />
              </div>
              <div class="config-row">
                <label class="config-label">Confidence Corrob. Weight</label>
                <input type="number" class="config-input" value={scoringConfig.confidenceCorrobWeight} step="0.01" min="0" max="1" disabled={backendStatus !== 'online'} oninput={(e) => updateScoring('confidenceCorrobWeight', Number(e.target.value))} />
              </div>
            </div>

            <!-- Classifier: Keyword Weight & De-escalation -->
            {#if classifierConfig}
            <div class="info-card">
              <h3 class="info-card-title">Classifier Tuning</h3>
              <div class="config-row">
                <label class="config-label">Keyword Weight</label>
                <input type="number" class="config-input" value={classifierConfig.keywordWeight} step="0.05" min="0.05" max="1" oninput={(e) => { classifierConfig.keywordWeight = Number(e.target.value); classifierDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">De-escalation Dampening</label>
                <input type="number" class="config-input" value={classifierConfig.deescalationDampening} step="0.05" min="0" max="1" oninput={(e) => { classifierConfig.deescalationDampening = Number(e.target.value); classifierDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Max Severity</label>
                <input type="number" class="config-input" value={classifierConfig.maxSeverity} step="1" min="1" max="10" oninput={(e) => { classifierConfig.maxSeverity = Number(e.target.value); classifierDirty = true; }} />
              </div>
              <div class="config-row">
                <label class="config-label">Max Weight</label>
                <input type="number" class="config-input" value={classifierConfig.maxWeight} step="0.1" min="0.1" max="5" oninput={(e) => { classifierConfig.maxWeight = Number(e.target.value); classifierDirty = true; }} />
              </div>
            </div>
            {/if}

            <!-- Classifier: Keyword Lists -->
            {#if classifierConfig}
            <div class="info-card">
              <h3 class="info-card-title">Keyword Lists</h3>
              <p class="m-0 mb-2 text-[0.65rem] text-muted">Comma-separated. Changes apply on next data refresh.</p>
              <div class="grid gap-3">
                <div>
                  <label class="config-label mb-1 block">De-escalation Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.deescalationKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('deescalationKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">Military Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.militaryKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('militaryKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">War Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.warKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('warKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">Civil Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.civilKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('civilKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">Terrorism Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.terrorismKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('terrorismKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">Humanitarian Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.humanitarianKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('humanitarianKeywords', e.target.value)}></textarea>
                </div>
                <div>
                  <label class="config-label mb-1 block">Narrative Keywords</label>
                  <textarea class="config-textarea" rows="2" value={(classifierConfig.narrativeKeywords ?? []).join(", ")} oninput={(e) => updateClassifierKeywords('narrativeKeywords', e.target.value)}></textarea>
                </div>
              </div>
            </div>
            {/if}
          </div>

          <div class="mt-4 flex items-center gap-3">
            <button type="button" class="admin-btn" disabled={backendStatus !== 'online' || (!scoringConfigDirty && !classifierDirty)} onclick={() => { if (scoringConfigDirty) saveScoringConfig(); if (classifierDirty) saveClassifierConfig(); }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              Save Configuration
            </button>
            <button type="button" class="admin-btn admin-btn-secondary" disabled={backendStatus !== 'online'} onclick={() => { resetScoringConfig(); resetClassifierConfig(); }}>
              Reset to Defaults
            </button>
            {#if scoringSaveMsg}
              <span class="font-mono text-[0.65rem] text-[#49d4ba]">{scoringSaveMsg}</span>
            {/if}
            {#if classifierSaveMsg}
              <span class="font-mono text-[0.65rem] text-[#49d4ba]">{classifierSaveMsg}</span>
            {/if}
          </div>

          {#if backendStatus !== 'online'}
          <p class="m-0 mt-3 font-mono text-[0.6rem] text-muted tracking-[0.06em]">
            Connect the backend to edit configuration.
          </p>
          {/if}
        </div>

      <!-- ═══════ ACTIVITY LOG ═══════ -->
      {:else if activeTab === "logs"}
        <div class="admin-section">
          <h2 class="admin-heading">Activity Log</h2>
          <p class="admin-desc">Audit trail of data refreshes, configuration changes, and system events.</p>

          <div class="log-list">
            <div class="log-entry">
              <span class="log-time">{generatedAt?.toLocaleTimeString() ?? "—"}</span>
              <span class="log-badge log-badge-info">DATA</span>
              <span>Generated osint-data.js — {totalItems} items from {sources.length} sources</span>
            </div>
            {#each failures as fail}
              <div class="log-entry">
                <span class="log-time">{generatedAt?.toLocaleTimeString() ?? "—"}</span>
                <span class="log-badge log-badge-error">ERROR</span>
                <span>Feed failure: {fail.id ?? fail.sourceId ?? "unknown"} — {fail.error ?? "fetch failed"}</span>
              </div>
            {/each}
            <div class="log-entry log-muted">
              <span class="log-time">—</span>
              <span class="log-badge log-badge-system">SYS</span>
              <span>Full activity logging requires backend API integration</span>
            </div>
          </div>
        </div>

      <!-- ═══════ USERS & ACCESS ═══════ -->
      {:else if activeTab === "users"}
        <div class="admin-section">
          <h2 class="admin-heading">Users & Access Control</h2>
          <p class="admin-desc">Manage analyst accounts, roles, and permissions.</p>

          <div class="placeholder-panel">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-muted opacity-30">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <p class="m-0 font-mono text-[0.72rem] text-muted tracking-[0.06em] text-center max-w-[380px]">
              User management and role-based access control will be available when authentication is configured.
            </p>
            <div class="flex gap-3 mt-3">
              <button type="button" class="admin-btn" disabled>Add User</button>
              <button type="button" class="admin-btn admin-btn-secondary" disabled>Configure SSO</button>
            </div>
          </div>
        </div>
      {/if}

    </main>
  </div>
</div>

<!-- Add Source Modal — rendered outside the animated container so position:fixed works against viewport -->
{#if addingPlatform}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="source-modal-backdrop" onclick={closeAddSource} onkeydown={(e) => e.key === 'Escape' && closeAddSource()}>
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="source-modal" onclick={(e) => e.stopPropagation()} onkeydown={() => {}}>
      <div class="source-modal-header">
        <div class="flex items-center gap-3">
          <div class="platform-icon-sm" style="--p-bg: {addingPlatform.bg}; --p-border: {addingPlatform.border};">
            <svg width="20" height="20" viewBox="0 0 24 24" fill={addingPlatform.id === 'x' ? addingPlatform.color : 'none'} stroke={addingPlatform.id === 'x' ? 'none' : addingPlatform.color} stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d={addingPlatform.icon} />
            </svg>
          </div>
          <div>
            <h3 class="m-0 text-[0.95rem] font-semibold">Add {addingPlatform.name} Source</h3>
            <p class="m-0 text-[0.7rem] text-muted">{addingPlatform.desc}</p>
          </div>
        </div>
        <button type="button" class="modal-close" onclick={closeAddSource}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>

      <div class="source-modal-body">
        <div class="modal-field">
          <label class="modal-label">Source Label</label>
          <input type="text" class="modal-input" bind:value={newSourceLabel} placeholder="e.g. OSINT Twitter List, BBC World RSS" />
        </div>

        {#if addingPlatform.id === "rss"}
          <div class="modal-field">
            <label class="modal-label">Feed URL</label>
            <input type="url" class="modal-input" bind:value={newSourceUrl} placeholder="https://example.com/feed.xml" />
          </div>
        {:else if addingPlatform.id === "google"}
          <div class="modal-field">
            <label class="modal-label">Search Query / Alert Keywords</label>
            <input type="text" class="modal-input" bind:value={newSourceKeywords} placeholder="e.g. military deployment Africa" />
          </div>
        {:else if addingPlatform.id === "x"}
          <div class="modal-field">
            <label class="modal-label">Account, List, or Search Query</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. @username, list:123456, keyword search" />
          </div>
        {:else if addingPlatform.id === "bluesky"}
          <div class="modal-field">
            <label class="modal-label">Handle or Feed URL</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. @user.bsky.social or feed URL" />
          </div>
        {:else if addingPlatform.id === "telegram"}
          <div class="modal-field">
            <label class="modal-label">Channel or Group Link</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. https://t.me/channel_name" />
          </div>
        {:else if addingPlatform.id === "reddit"}
          <div class="modal-field">
            <label class="modal-label">Subreddit or Search Query</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. r/worldnews, r/geopolitics, keyword search" />
          </div>
        {:else if addingPlatform.id === "youtube"}
          <div class="modal-field">
            <label class="modal-label">Channel URL or Search Query</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. https://youtube.com/@channel" />
          </div>
        {:else if addingPlatform.id === "mastodon"}
          <div class="modal-field">
            <label class="modal-label">Account or Instance Hashtag</label>
            <input type="text" class="modal-input" bind:value={newSourceUrl} placeholder="e.g. @user@instance.social, #hashtag" />
          </div>
        {/if}

        <div class="modal-field">
          <label class="modal-label">Keywords Filter <span class="text-muted">(optional)</span></label>
          <input type="text" class="modal-input" bind:value={newSourceKeywords} placeholder="Comma-separated keywords to filter by" />
        </div>
      </div>

      <div class="source-modal-footer">
        <button type="button" class="admin-btn admin-btn-secondary" onclick={closeAddSource}>Cancel</button>
        <button
          type="button"
          class="admin-btn"
          disabled={!newSourceLabel.trim()}
          onclick={submitNewSource}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          Add Source
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* ── Env Warning Banner ── */
  .env-warning-banner {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    background: rgba(255, 178, 95, 0.1);
    border: 1px solid rgba(255, 178, 95, 0.35);
    border-radius: 4px;
    font-size: 0.78rem;
    line-height: 1.5;
    color: #ffb25f;
  }
  .env-warning-icon {
    font-size: 1.1rem;
    line-height: 1;
    flex-shrink: 0;
    margin-top: 1px;
  }

  /* ── Admin Layout ── */
  .admin-layout {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 0;
    min-height: 70vh;
  }
  @media (max-width: 820px) {
    .admin-layout {
      grid-template-columns: 1fr;
    }
  }

  .admin-sidebar {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-right: 20px;
    border-right: 1px solid var(--color-rule);
  }
  @media (max-width: 820px) {
    .admin-sidebar {
      flex-direction: row;
      flex-wrap: wrap;
      gap: 4px;
      padding-right: 0;
      padding-bottom: 16px;
      border-right: none;
      border-bottom: 1px solid var(--color-rule);
      margin-bottom: 16px;
    }
  }

  .admin-tab {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: none;
    border: 1px solid transparent;
    color: var(--color-muted);
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.06em;
    text-align: left;
    cursor: pointer;
    transition: all 0.15s;
  }
  .admin-tab:hover {
    color: var(--color-text);
    background: rgba(120, 214, 255, 0.03);
  }
  .admin-tab-active {
    color: var(--color-blue);
    background: rgba(120, 214, 255, 0.06);
    border-color: rgba(120, 214, 255, 0.16);
  }

  .admin-content {
    padding-left: 24px;
  }
  @media (max-width: 820px) {
    .admin-content { padding-left: 0; }
  }

  /* ── Section styles ── */
  .admin-section { }
  .admin-heading {
    margin: 8px 0 6px;
    font-size: 1.1rem;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  .admin-desc {
    margin: 0 0 28px;
    color: var(--color-muted);
    font-size: 0.82rem;
  }

  /* ── Stat cells ── */
  .stat-cell {
    padding: 16px 20px;
    display: grid;
    gap: 6px;
  }
  .stat-label {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-muted);
  }
  .stat-value {
    font-size: 1.4rem;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }

  /* ── Table ── */
  .admin-table-wrap {
    overflow-x: auto;
    border: 1px solid var(--color-line);
  }
  .admin-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.78rem;
  }
  .admin-table th {
    padding: 10px 14px;
    text-align: left;
    font-family: var(--font-mono);
    font-size: 0.6rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--color-muted);
    background: rgba(6, 12, 22, 0.4);
    border-bottom: 1px solid var(--color-line);
  }
  .admin-table td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--color-line);
    vertical-align: middle;
  }
  .admin-table tbody tr:hover {
    background: rgba(120, 214, 255, 0.02);
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
  }

  .status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 6px;
  }
  .status-healthy { background: var(--color-civil); box-shadow: 0 0 6px rgba(73, 212, 186, 0.4); }
  .status-error { background: var(--color-military); box-shadow: 0 0 6px rgba(255, 117, 87, 0.4); }
  .status-empty { background: var(--color-muted); }

  /* ── Buttons ── */
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
  .action-btn:hover:not(:disabled) {
    background: rgba(120, 214, 255, 0.12);
  }
  .action-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }
  .action-danger {
    color: var(--color-military);
    border-color: rgba(255, 117, 87, 0.15);
    background: rgba(255, 117, 87, 0.04);
  }
  .action-danger:hover:not(:disabled) {
    background: rgba(255, 117, 87, 0.1);
  }

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

  /* ── Info cards ── */
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
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid rgba(138, 166, 196, 0.06);
    font-size: 0.78rem;
    color: var(--color-body-light);
  }
  .info-row:last-child { border-bottom: none; }
  .info-row span:first-child { color: var(--color-muted); }

  /* ── Config rows ── */
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
  }
  .config-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* ── Log entries ── */
  .log-list {
    border: 1px solid var(--color-line);
  }
  .log-entry {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--color-line);
    font-size: 0.78rem;
    color: var(--color-body-light);
  }
  .log-entry:last-child { border-bottom: none; }
  .log-muted { color: var(--color-muted); font-style: italic; }
  .log-time {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--color-muted);
    min-width: 70px;
  }
  .log-badge {
    display: inline-block;
    padding: 2px 8px;
    font-family: var(--font-mono);
    font-size: 0.55rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    min-width: 48px;
    text-align: center;
  }
  .log-badge-info {
    background: rgba(120, 214, 255, 0.08);
    border: 1px solid rgba(120, 214, 255, 0.2);
    color: var(--color-blue);
  }
  .log-badge-error {
    background: rgba(255, 117, 87, 0.08);
    border: 1px solid rgba(255, 117, 87, 0.2);
    color: var(--color-military);
  }
  .log-badge-system {
    background: rgba(138, 166, 196, 0.06);
    border: 1px solid var(--color-line);
    color: var(--color-muted);
  }

  /* ── Platform Grid ── */
  .platform-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 24px;
  }
  @media (max-width: 1000px) {
    .platform-grid { grid-template-columns: repeat(3, 1fr); }
  }
  @media (max-width: 700px) {
    .platform-grid { grid-template-columns: repeat(2, 1fr); }
  }

  .platform-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 20px 12px 16px;
    background: var(--p-bg);
    border: 1px solid var(--p-border);
    cursor: pointer;
    transition: all 0.18s;
    text-align: center;
  }
  .platform-card:hover {
    background: color-mix(in srgb, var(--p-bg) 100%, rgba(255,255,255,0.03));
    border-color: var(--p-color);
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  }

  .platform-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid var(--p-border);
    border-radius: 10px;
    margin-bottom: 4px;
  }

  .platform-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--color-text);
    line-height: 1.2;
  }

  .platform-desc {
    font-family: var(--font-mono);
    font-size: 0.58rem;
    color: var(--color-muted);
    letter-spacing: 0.04em;
  }

  .platform-count {
    margin-top: 2px;
    padding: 2px 10px;
    font-family: var(--font-mono);
    font-size: 0.55rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--color-civil);
    background: rgba(73, 212, 186, 0.08);
    border: 1px solid rgba(73, 212, 186, 0.2);
  }

  .platform-add {
    margin-top: 2px;
    padding: 2px 10px;
    font-family: var(--font-mono);
    font-size: 0.55rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--p-color);
    opacity: 0.6;
    transition: opacity 0.15s;
  }
  .platform-card:hover .platform-add {
    opacity: 1;
  }

  /* ── Add Source Modal ── */
  .source-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 2000;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(6px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .source-modal {
    width: 100%;
    max-width: 520px;
    background: #0a1019;
    border: 1px solid var(--color-line);
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.6);
  }

  .source-modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-line);
  }

  .platform-icon-sm {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--p-bg);
    border: 1px solid var(--p-border);
    border-radius: 8px;
  }

  .modal-close {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: 1px solid transparent;
    color: var(--color-muted);
    cursor: pointer;
    transition: all 0.15s;
  }
  .modal-close:hover {
    color: var(--color-text);
    border-color: var(--color-line);
  }

  .source-modal-body {
    padding: 20px 24px;
    display: grid;
    gap: 16px;
  }

  .modal-field {
    display: grid;
    gap: 6px;
  }

  .modal-label {
    font-family: var(--font-mono);
    font-size: 0.62rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--color-muted);
  }

  .modal-input {
    width: 100%;
    padding: 10px 14px;
    background: rgba(6, 12, 22, 0.6);
    border: 1px solid var(--color-line);
    color: var(--color-text);
    font-family: var(--font-mono);
    font-size: 0.78rem;
    letter-spacing: 0.02em;
    outline: none;
    transition: border-color 0.15s;
  }
  .modal-input::placeholder {
    color: var(--color-muted);
    opacity: 0.5;
  }
  .modal-input:focus {
    border-color: rgba(120, 214, 255, 0.4);
  }

  .source-modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 16px 24px;
    border-top: 1px solid var(--color-line);
  }

  /* ── Placeholder panel ── */
  .placeholder-panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 24px;
    border: 1px dashed var(--color-line);
    background: rgba(6, 12, 22, 0.2);
  }

  /* ── AI Config extras ── */
  .config-input-wide {
    width: 220px;
  }
  @media (max-width: 820px) {
    .config-input-wide { width: 160px; }
  }

  .config-textarea {
    width: 100%;
    padding: 10px 12px;
    background: rgba(6, 12, 22, 0.5);
    border: 1px solid var(--color-line);
    color: var(--color-text);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    line-height: 1.6;
    letter-spacing: 0.02em;
    resize: vertical;
    outline: none;
    transition: border-color 0.15s;
  }
  .config-textarea:focus {
    border-color: rgba(120, 214, 255, 0.4);
  }

  .ai-toggle {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(138, 166, 196, 0.06);
    cursor: pointer;
  }
  .ai-toggle:last-child { border-bottom: none; }
  .ai-toggle input[type="checkbox"] {
    width: 16px;
    height: 16px;
    margin-top: 2px;
    accent-color: var(--color-blue);
    cursor: pointer;
    flex-shrink: 0;
  }
  .ai-toggle-label {
    display: block;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--color-text);
  }
  .ai-toggle-desc {
    display: block;
    font-size: 0.65rem;
    color: var(--color-muted);
    margin-top: 1px;
  }
</style>
