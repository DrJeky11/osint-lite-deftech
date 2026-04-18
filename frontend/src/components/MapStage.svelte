<script>
  import { onMount } from "svelte";
  import maplibregl from "maplibre-gl";
  import { filters, selection, getFilteredSignalEvents, getVisibleScores, ensureValidSelection } from "../state.svelte.js";
  import { scoresToGeoJSON, signalEventsToGeoJSON } from "../lib/geojson.js";
  import {
    OVERLAY_REGISTRY,
    loadOverlayPreferences,
    addOverlayLayers,
    setOverlayVisibility,
  } from "../lib/overlays.js";
  import { applyMapTheme } from "../lib/mapTheme.js";
  import OverlayPanel from "./OverlayPanel.svelte";

  let { onDataUpdate = () => {} } = $props();

  let container;
  let map;
  let loaded = false;
  let overlayPrefs = loadOverlayPreferences();

  onMount(() => {
    map = new maplibregl.Map({
      container,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [32, 10],
      zoom: 2,
      attributionControl: false,
      maxZoom: 12,
      minZoom: 1
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    map.on("load", () => {
      map.setProjection({ type: filters.projection === "globe" ? "globe" : "mercator" });
      setupSources();
      setupLayers();
      setupInteractivity();

      try {
        setupOverlaySources();
        setupOverlayLayers();
      } catch (err) {
        console.warn("Overlay setup failed:", err);
      }

      applyMapTheme(map);
      loaded = true;
      updateMapData();
    });

    window.addEventListener("resize", handleResize);

    return () => {
      map.off("click", "hotspot-circles", handleHotspotClick);
      map.off("mouseenter", "hotspot-circles", handleHotspotEnter);
      map.off("mouseleave", "hotspot-circles", handleHotspotLeave);
      window.removeEventListener("resize", handleResize);
      map.remove();
    };
  });

  function handleResize() {
    if (map) map.resize();
  }

  function setupSources() {
    map.addSource("signal-events", {
      type: "geojson",
      data: signalEventsToGeoJSON([])
    });
    map.addSource("hotspots", {
      type: "geojson",
      data: scoresToGeoJSON([]),
      generateId: true
    });
  }

  function setupOverlaySources() {
    for (const overlay of OVERLAY_REGISTRY) {
      map.addSource(overlay.id, {
        type: "geojson",
        data: overlay.dataUrl
      });
    }
  }

  function setupOverlayLayers() {
    for (const overlay of OVERLAY_REGISTRY) {
      addOverlayLayers(map, overlay.id, overlayPrefs[overlay.id]);
    }
  }

  function handleOverlayToggle(id, visible) {
    overlayPrefs[id] = visible;
    if (map && loaded) {
      setOverlayVisibility(map, id, visible);
    }
  }

  function setupLayers() {
    map.addLayer({
      id: "signal-heatmap",
      type: "heatmap",
      source: "signal-events",
      paint: {
        "heatmap-weight": ["get", "weight"],
        "heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 1, 0.6, 6, 1.2, 10, 2],
        "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 1, 20, 6, 35, 10, 50],
        "heatmap-color": [
          "interpolate", ["linear"], ["heatmap-density"],
          0,    "rgba(0, 0, 0, 0)",
          0.1,  "rgba(10, 60, 120, 0.35)",
          0.25, "rgba(20, 140, 210, 0.5)",
          0.4,  "rgba(73, 212, 186, 0.6)",
          0.6,  "rgba(180, 210, 140, 0.7)",
          0.8,  "rgba(255, 178, 95, 0.85)",
          1.0,  "rgba(255, 80, 50, 0.95)"
        ],
        "heatmap-opacity": 0.75
      }
    });

    map.addLayer({
      id: "hotspot-glow",
      type: "circle",
      source: "hotspots",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "heat"], 0, 14, 50, 24, 100, 40],
        "circle-color": ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#ffb25f", 100, "#ff7557"],
        "circle-opacity": 0.14,
        "circle-blur": 0.9
      }
    });

    map.addLayer({
      id: "hotspot-circles",
      type: "circle",
      source: "hotspots",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "heat"], 0, 6, 50, 11, 100, 18],
        "circle-color": ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#ffb25f", 100, "#ff7557"],
        "circle-opacity": 0.88,
        "circle-stroke-width": 0,
        "circle-stroke-color": "rgba(255, 255, 255, 0.92)",
        "circle-blur": 0.1
      }
    });

    map.addLayer({
      id: "hotspot-center",
      type: "circle",
      source: "hotspots",
      paint: {
        "circle-radius": 3,
        "circle-color": "rgba(245, 250, 255, 0.96)",
        "circle-opacity": 0.95
      }
    });

    map.addLayer({
      id: "hotspot-labels",
      type: "symbol",
      source: "hotspots",
      layout: {
        "text-field": ["upcase", ["get", "name"]],
        "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
        "text-size": 11,
        "text-offset": [0, -2.2],
        "text-anchor": "bottom",
        "text-allow-overlap": true
      },
      paint: {
        "text-color": "#f5f8ff",
        "text-halo-color": "rgba(4, 9, 16, 0.92)",
        "text-halo-width": 2
      },
      filter: ["==", ["get", "id"], ""]
    });
  }

  function handleHotspotClick(event) {
    const feature = event.features[0];
    if (feature) {
      selectHotspot(feature.properties.id);
    }
  }

  function handleHotspotEnter() {
    map.getCanvas().style.cursor = "pointer";
  }

  function handleHotspotLeave() {
    map.getCanvas().style.cursor = "";
  }

  function setupInteractivity() {
    map.on("click", "hotspot-circles", handleHotspotClick);
    map.on("mouseenter", "hotspot-circles", handleHotspotEnter);
    map.on("mouseleave", "hotspot-circles", handleHotspotLeave);
  }

  export function selectHotspot(scoreId) {
    selection.locationId = scoreId;
    updateSelectedStyling();

    const visibleScores = getVisibleScores();
    const score = visibleScores.find((s) => s.id === scoreId);
    if (score) {
      map.flyTo({
        center: [score.center.lon, score.center.lat],
        zoom: Math.max(map.getZoom(), 4),
        duration: 1200
      });
    }
  }

  function updateSelectedStyling() {
    if (!map || !map.getLayer("hotspot-circles")) return;

    map.setPaintProperty("hotspot-circles", "circle-stroke-width", [
      "case",
      ["==", ["get", "id"], selection.locationId || ""],
      2.2,
      0
    ]);

    map.setFilter("hotspot-labels", [
      "==", ["get", "id"], selection.locationId || ""
    ]);
  }

  export function updateMapData() {
    if (!loaded || !map || !map.getSource("signal-events")) return;

    const visibleScores = getVisibleScores();
    ensureValidSelection(visibleScores);

    const filteredEvents = getFilteredSignalEvents();
    map.getSource("signal-events").setData(signalEventsToGeoJSON(filteredEvents));
    map.getSource("hotspots").setData(scoresToGeoJSON(visibleScores));

    map.setLayoutProperty("signal-heatmap", "visibility",
      filters.heatmapEnabled ? "visible" : "none"
    );

    updateSelectedStyling();
    onDataUpdate(visibleScores, filteredEvents);
  }

  export function applyProjection() {
    if (!map) return;
    map.setProjection({ type: filters.projection === "globe" ? "globe" : "mercator" });
  }
</script>

<div class="relative min-h-[620px] overflow-hidden border border-line max-[820px]:min-h-[460px]"
  style="background: linear-gradient(180deg, rgba(8, 16, 27, 0.98), rgba(2, 6, 12, 0.98))"
>
  <!-- Scan-line overlay -->
  <div class="absolute inset-0 pointer-events-none z-1 opacity-40"
    style="background: repeating-linear-gradient(0deg, transparent 0 3px, rgba(120, 214, 255, 0.015) 3px 4px)"
  ></div>

  <!-- Sweep line -->
  <div class="absolute inset-0 pointer-events-none z-1 animate-[sweep_14s_linear_infinite]"
    style="background: linear-gradient(180deg, transparent, rgba(120, 214, 255, 0.03) 48%, transparent)"
  ></div>

  <!-- Map header -->
  <div class="absolute inset-x-0 top-0 flex justify-between items-start gap-4 px-5 py-4 pointer-events-none z-2 max-[820px]:grid max-[820px]:gap-2 max-[820px]:p-3">
    <div>
      <p class="font-mono text-[0.6rem] tracking-[0.16em] uppercase text-muted m-0">Global signal surface</p>
    </div>
    <div class="inline-flex items-center gap-2.5 px-3 py-2 border border-[rgba(120,214,255,0.12)] bg-[rgba(3,8,15,0.6)]" aria-hidden="true">
      <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">Low</span>
      <span class="w-[100px] h-2" style="background: linear-gradient(90deg, #49d4ba 0%, #ffb25f 55%, #ff7557 100%)"></span>
      <span class="font-mono text-[0.55rem] tracking-[0.14em] uppercase text-muted">High</span>
    </div>
  </div>

  <!-- MapLibre container -->
  <div bind:this={container} id="map-container" class="absolute inset-0 z-0" aria-label="Interactive map showing instability hotspots"></div>

  <!-- Overlay panel -->
  <OverlayPanel onToggle={handleOverlayToggle} />
</div>
