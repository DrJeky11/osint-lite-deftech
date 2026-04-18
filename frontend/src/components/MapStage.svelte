<script>
  import { onMount } from "svelte";
  import maplibregl from "maplibre-gl";
  import { filters, selection, getFilteredSignalEvents, getVisibleScores, ensureValidSelection } from "../state.svelte.js";
  import { scoresToGeoJSON, signalEventsToGeoJSON, countryFillGeoJSON, resolveCountryName } from "../lib/geojson.js";
  import {
    OVERLAY_REGISTRY,
    loadOverlayPreferences,
    addOverlayLayers,
    setOverlayVisibility,
    buildOverlayTooltip,
    getOverlayInteractiveLayerId,
  } from "../lib/overlays.js";
  import { applyMapTheme } from "../lib/mapTheme.js";
  import { loadFlagImage } from "../lib/flagImage.js";


  let { onDataUpdate = () => {}, fullBleed = false } = $props();

  let container;
  let map;
  let loaded = false;
  let overlayPrefs = loadOverlayPreferences();
  let hoverPopup = null;
  let countriesGeoJSON = null;

  onMount(() => {
    if (!container) {
      console.error("[MapStage] container ref is null — bind:this failed");
      return;
    }
    console.log("[MapStage] init, container size:", container.clientWidth, "x", container.clientHeight);

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

    hoverPopup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      className: "sa-popup",
      maxWidth: "280px",
      offset: 12
    });

    map.on("error", (e) => {
      console.error("[MapStage] map error:", e.error?.message || e);
    });

    map.on("load", () => {
      console.log("[MapStage] map loaded successfully");
      map.setProjection({ type: filters.projection === "globe" ? "globe" : "mercator" });
      setupSources();

      // Register flag image handler BEFORE layers that reference flag-* icons
      map.on("styleimagemissing", (e) => {
        if (e.id.startsWith("flag-")) {
          const countryCode = e.id.replace("flag-", "");
          loadFlagImage(map, countryCode).then(() => {
            map.triggerRepaint();
          });
        }
      });

      setupOverlaySources();
      setupOverlayLayers();
      setupOverlayInteractivity();

      // Country choropleth fill — added before hotspot layers so dots render on top
      setupCountryFillLayers();

      setupLayers();
      setupInteractivity();

      applyMapTheme(map);
      loaded = true;

      // Load the countries GeoJSON, then trigger initial data render
      fetch("/overlays/countries.json")
        .then((r) => r.json())
        .then((geojson) => {
          countriesGeoJSON = geojson;
          updateMapData();
        })
        .catch((err) => {
          console.warn("[MapStage] could not load countries.json:", err);
          updateMapData();
        });
    });

    window.addEventListener("resize", handleResize);

    return () => {
      hoverPopup?.remove();
      map.off("click", "hotspot-circles", handleHotspotClick);
      map.off("mousemove", "hotspot-circles", handleHotspotHover);
      map.off("mouseleave", "hotspot-circles", handleHotspotLeave);
      window.removeEventListener("resize", handleResize);
      map.remove();
    };
  });

  function handleResize() {
    if (map) map.resize();
  }

  function setupSources() {
    map.addSource("country-fill", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] }
    });
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

  export function handleOverlayToggle(id, visible) {
    overlayPrefs[id] = visible;
    if (map && loaded) {
      setOverlayVisibility(map, id, visible);
    }
  }

  function setupCountryFillLayers() {
    // Fill layer — lighter colors, always visible for all countries
    map.addLayer({
      id: "country-fill",
      type: "fill",
      source: "country-fill",
      paint: {
        "fill-color": [
          "case",
          ["==", ["get", "trend"], "warming"],
          ["interpolate", ["linear"], ["get", "heat"],
            0,   "#1e1810",
            15,  "#3d2c14",
            30,  "#6b4a1e",
            50,  "#c47a2a",
            70,  "#e8943a",
            100, "#ffb25f"
          ],
          ["==", ["get", "trend"], "cooling"],
          ["interpolate", ["linear"], ["get", "heat"],
            0,   "#101e1a",
            15,  "#183328",
            30,  "#245040",
            50,  "#2f7a60",
            70,  "#3ba882",
            100, "#49d4ba"
          ],
          ["==", ["get", "trend"], "steady"],
          ["interpolate", ["linear"], ["get", "heat"],
            0,   "#141820",
            15,  "#1e2430",
            30,  "#2e3648",
            50,  "#455570",
            70,  "#5a7090",
            100, "#7a94b5"
          ],
          // default: no data — very subtle base fill
          "#111620"
        ],
        "fill-opacity": [
          "case",
          ["==", ["get", "hasData"], true],
          ["interpolate", ["linear"], ["get", "heat"],
            0,   0.20,
            30,  0.30,
            60,  0.42,
            100, 0.55
          ],
          0.15  // base opacity for countries with no data
        ]
      }
    });

    // Border layer — always visible on all countries
    map.addLayer({
      id: "country-fill-border",
      type: "line",
      source: "country-fill",
      paint: {
        "line-color": [
          "case",
          ["==", ["get", "trend"], "warming"], "rgba(255, 178, 95, 0.50)",
          ["==", ["get", "trend"], "cooling"], "rgba(73, 212, 186, 0.45)",
          ["==", ["get", "trend"], "steady"],  "rgba(140, 160, 190, 0.40)",
          "rgba(80, 100, 130, 0.30)"  // no-data countries: subtle but visible outline
        ],
        "line-width": [
          "case",
          ["==", ["get", "hasData"], true], 1.2,
          0.6  // thinner for no-data countries
        ],
        "line-opacity": 1
      }
    });

    // Highlight border for selected country
    map.addLayer({
      id: "country-fill-highlight",
      type: "line",
      source: "country-fill",
      paint: {
        "line-color": "#ffb25f",
        "line-width": 2.5,
        "line-opacity": 0.9,
      },
      filter: ["==", ["get", "name"], ""],
    });
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
        "heatmap-opacity": 0.40
      }
    });

    map.addLayer({
      id: "hotspot-glow",
      type: "circle",
      source: "hotspots",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "heat"], 0, 8, 50, 14, 100, 24],
        "circle-color": [
          "case",
          ["==", ["get", "trend"], "warming"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#ffb25f", 50, "#ff7557", 100, "#ff4030"],
          ["==", ["get", "trend"], "cooling"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#49d4ba", 100, "#ffb25f"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#ffb25f", 100, "#ff7557"]
        ],
        "circle-opacity": 0.08,
        "circle-blur": 0.9
      }
    });

    map.addLayer({
      id: "hotspot-circles",
      type: "circle",
      source: "hotspots",
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["get", "heat"], 0, 4, 50, 8, 100, 13],
        "circle-color": [
          "case",
          ["==", ["get", "trend"], "warming"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#ffb25f", 50, "#ff7557", 100, "#ff4030"],
          ["==", ["get", "trend"], "cooling"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#49d4ba", 100, "#ffb25f"],
          ["interpolate", ["linear"], ["get", "heat"], 0, "#49d4ba", 50, "#ffb25f", 100, "#ff7557"]
        ],
        "circle-opacity": 0.70,
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
        "circle-radius": 2,
        "circle-color": "rgba(245, 250, 255, 0.96)",
        "circle-opacity": 0.80
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

  function buildCountryTooltip(props) {
    const trendColor = props.trend === "warming" ? "#ffb25f"
      : props.trend === "cooling" ? "#49d4ba" : "#d3dde8";
    return `
      <div style="font-family:'DM Sans',sans-serif; padding:6px 2px;">
        <div style="font-size:13px; font-weight:600; margin-bottom:6px; color:#e2e8f0;">
          ${props.name}
        </div>
        <div style="display:grid; grid-template-columns:auto 1fr; gap:2px 10px; font-size:11px;">
          <span style="color:#78d6ff99;">Heat</span>
          <span style="color:#e2e8f0; font-family:'DM Mono',monospace;">${Math.round(props.heat)}</span>
          <span style="color:#78d6ff99;">Delta</span>
          <span style="color:#e2e8f0; font-family:'DM Mono',monospace;">${props.delta > 0 ? "+" : ""}${props.delta}</span>
          <span style="color:#78d6ff99;">Trend</span>
          <span style="color:${trendColor}; font-family:'DM Mono',monospace; text-transform:uppercase; font-size:10px;">${props.trend}</span>
        </div>
      </div>`;
  }

  function buildHotspotTooltip(props) {
    const trendColor = props.trend === "warming" ? "#ff7557" : props.trend === "cooling" ? "#49d4ba" : "#d3dde8";
    const deltaSign = props.delta > 0 ? "+" : "";
    const dominant = props.militaryComponent > props.civilComponent + 8
      ? "Military-led"
      : props.civilComponent > props.militaryComponent + 8
        ? "Civil-led"
        : "Mixed signal";

    return `<div style="font-family:'SF Mono','IBM Plex Mono',monospace;font-size:11px;line-height:1.5;min-width:180px">` +
      `<div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:#ffb25f;margin-bottom:4px">Priority theater</div>` +
      `<div style="font-size:13px;font-weight:700;color:#f0f4fb;margin-bottom:8px">${props.name}</div>` +
      `<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 12px">` +
        `<div><span style="color:#8a9db5">Heat</span></div><div style="text-align:right;font-weight:600">${Math.round(props.heat)}</div>` +
        `<div><span style="color:#8a9db5">Delta</span></div><div style="text-align:right;font-weight:600">${deltaSign}${Math.round(props.delta)}</div>` +
        `<div><span style="color:#8a9db5">Trend</span></div><div style="text-align:right;font-weight:600;color:${trendColor}">${props.trend}</div>` +
        `<div><span style="color:#8a9db5">Confidence</span></div><div style="text-align:right">${Math.round(props.confidence * 100)}%</div>` +
      `</div>` +
      `<div style="margin-top:8px;padding-top:6px;border-top:1px solid rgba(138,166,196,0.14)">` +
        `<div style="display:flex;justify-content:space-between"><span style="color:#49d4ba">Civil</span><span>${Math.round(props.civilComponent)}</span></div>` +
        `<div style="display:flex;justify-content:space-between"><span style="color:#ff7557">Military</span><span>${Math.round(props.militaryComponent)}</span></div>` +
        `<div style="margin-top:4px;font-size:10px;color:#8a9db5">${dominant} pressure profile</div>` +
      `</div>` +
    `</div>`;
  }

  function handleHotspotHover(event) {
    const feature = event.features[0];
    if (!feature) return;
    map.getCanvas().style.cursor = "pointer";
    hoverPopup
      .setLngLat(feature.geometry.coordinates)
      .setHTML(buildHotspotTooltip(feature.properties))
      .addTo(map);
  }

  function handleHotspotLeave() {
    map.getCanvas().style.cursor = "";
    hoverPopup.remove();
  }

  function setupOverlayInteractivity() {
    for (const overlay of OVERLAY_REGISTRY) {
      const layerId = getOverlayInteractiveLayerId(overlay.id);
      if (!layerId || !map.getLayer(layerId)) continue;

      map.on("mouseenter", layerId, (event) => {
        const feature = event.features[0];
        if (!feature) return;
        map.getCanvas().style.cursor = "pointer";

        const coords = feature.geometry.type === "Point"
          ? feature.geometry.coordinates.slice()
          : [event.lngLat.lng, event.lngLat.lat];

        hoverPopup
          .setLngLat(coords)
          .setHTML(buildOverlayTooltip(overlay.id, feature.properties))
          .addTo(map);
      });

      map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "";
        hoverPopup.remove();
      });
    }
  }

  function setupInteractivity() {
    // General click with bbox tolerance for mobile touch
    map.on("click", (e) => {
      const pad = 20;
      const bbox = [[e.point.x - pad, e.point.y - pad], [e.point.x + pad, e.point.y + pad]];
      const features = map.queryRenderedFeatures(bbox, {
        layers: ["hotspot-circles", "hotspot-glow", "hotspot-center"]
      });
      if (features.length > 0) {
        selectHotspot(features[0].properties.id);
        return;
      }
      // Fallback: check country fill
      const countryFeatures = map.queryRenderedFeatures(e.point, {
        layers: ["country-fill"]
      });
      if (countryFeatures.length > 0) {
        const countryName = countryFeatures[0].properties.name;
        if (countryName) selectCountry(countryName);
      }
    });
    map.on("mousemove", "hotspot-circles", handleHotspotHover);
    map.on("mouseleave", "hotspot-circles", handleHotspotLeave);

    map.on("mousemove", "country-fill", (e) => {
      if (!e.features?.length) return;
      // Skip if hovering over a hotspot (points take priority)
      const hotspotFeatures = map.queryRenderedFeatures(e.point, {
        layers: ["hotspot-circles", "hotspot-glow", "hotspot-center"]
      });
      if (hotspotFeatures.length > 0) return;

      const props = e.features[0].properties;
      if (!props.hasData || props.hasData === "false") return;
      map.getCanvas().style.cursor = "pointer";
      hoverPopup
        .setLngLat([e.lngLat.lng, e.lngLat.lat])
        .setHTML(buildCountryTooltip(props))
        .addTo(map);
    });

    map.on("mouseleave", "country-fill", () => {
      map.getCanvas().style.cursor = "";
      hoverPopup.remove();
    });
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

  function selectCountry(countryName) {
    const visibleScores = getVisibleScores();
    const match = visibleScores.find(s => {
      const resolved = resolveCountryName(s);
      return resolved?.toLowerCase() === countryName.toLowerCase()
        || s.name?.toLowerCase() === countryName.toLowerCase();
    });
    if (match) {
      selection.locationId = match.id;
      updateSelectedStyling();
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

    // Find selected score's country for highlight border
    const visibleScores = getVisibleScores();
    const selectedScore = visibleScores.find(s => s.id === selection.locationId);
    const selectedCountry = selectedScore ? resolveCountryName(selectedScore) : "";
    if (map.getLayer("country-fill-highlight")) {
      map.setFilter("country-fill-highlight", ["==", ["get", "name"], selectedCountry || ""]);
    }
  }

  export function updateMapData() {
    if (!loaded || !map || !map.getSource("signal-events")) return;

    const visibleScores = getVisibleScores();
    ensureValidSelection(visibleScores);

    const filteredEvents = getFilteredSignalEvents();
    map.getSource("signal-events").setData(signalEventsToGeoJSON(filteredEvents));
    map.getSource("hotspots").setData(scoresToGeoJSON(visibleScores));

    // Update country choropleth fill when countries GeoJSON is available
    if (countriesGeoJSON && map.getSource("country-fill")) {
      map.getSource("country-fill").setData(countryFillGeoJSON(visibleScores, countriesGeoJSON));
    }

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

<div class={fullBleed ? "relative h-full w-full overflow-hidden" : "relative h-[620px] overflow-hidden border border-line max-[820px]:h-[460px]"}
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

</div>
