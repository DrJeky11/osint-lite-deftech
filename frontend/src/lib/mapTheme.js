/**
 * Reskin CartoDB Dark Matter basemap layers to match the app's
 * deep navy-blue theme palette.
 *
 * Theme tokens (from CSS vars):
 *   --bg:          #050913
 *   --bg-deep:     #02050b
 *   --line:        rgba(138,166,196,0.14)
 *   --line-strong: rgba(132,208,255,0.28)
 *   --muted:       #91a3bb
 *   --text:        #f3f7ff
 *   --blue:        #78d6ff
 *   --blue-strong: #2d95c7
 *   --amber:       #ffb25f
 */

const THEME = {
  bg:        "#1a2d4a",
  bgDeep:    "#142440",
  land:      "#1e3352",
  landAlt:   "#243a58",
  water:     "#0c1826",
  waterLine: "rgba(45, 149, 199, 0.35)",
  parkFill:  "rgba(73, 212, 186, 0.12)",
  boundary:  "rgba(132, 208, 255, 0.38)",
  boundaryDisputed: "rgba(255, 178, 95, 0.30)",
  roadMajor:    "rgba(160, 190, 220, 0.30)",
  roadMinor:    "rgba(140, 170, 200, 0.16)",
  roadHighway:  "rgba(132, 208, 255, 0.35)",
  building:     "rgba(140, 175, 210, 0.12)",
  labelPrimary: "rgba(243, 247, 255, 0.90)",
  labelSecondary: "rgba(160, 185, 210, 0.78)",
  labelWater:   "rgba(80, 180, 230, 0.62)",
  labelHalo:    "rgba(10, 18, 32, 0.85)",
};

/**
 * Apply theme colours to every basemap layer in the current style.
 * Safe to call on any MapLibre map using a vector basemap.
 */
export function applyMapTheme(map) {
  const style = map.getStyle();
  if (!style || !style.layers) return;

  for (const layer of style.layers) {
    const id = layer.id;
    const type = layer.type;
    const sl = layer["source-layer"] || "";

    try {
      // --- Background ---
      if (type === "background") {
        map.setPaintProperty(id, "background-color", THEME.bg);
        continue;
      }

      // --- Water fills ---
      if (type === "fill" && sl === "water") {
        map.setPaintProperty(id, "fill-color", THEME.water);
        continue;
      }

      // --- Waterway lines ---
      if (type === "line" && sl === "waterway") {
        map.setPaintProperty(id, "line-color", THEME.waterLine);
        continue;
      }

      // --- Landcover / landuse ---
      if (type === "fill" && (sl === "landcover" || sl === "landuse")) {
        const isPark = id.includes("park") || id.includes("green") || id.includes("wood") || id.includes("forest");
        map.setPaintProperty(id, "fill-color", isPark ? THEME.parkFill : THEME.landAlt);
        continue;
      }

      // --- Land / earth polygons ---
      if (type === "fill" && !layer.source) {
        map.setPaintProperty(id, "fill-color", THEME.land);
        continue;
      }

      // --- Buildings ---
      if (type === "fill" && sl === "building") {
        map.setPaintProperty(id, "fill-color", THEME.building);
        continue;
      }

      // --- Boundaries ---
      if (type === "line" && (sl === "boundary" || id.includes("boundary") || id.includes("admin"))) {
        const disputed = id.includes("disputed") || id.includes("dash");
        map.setPaintProperty(id, "line-color", disputed ? THEME.boundaryDisputed : THEME.boundary);
        continue;
      }

      // --- Roads, tunnels, bridges ---
      if (type === "line" && (sl === "transportation" || id.includes("road") || id.includes("tunnel") || id.includes("bridge") || id.includes("rail") || id.includes("transit"))) {
        const isHighway = id.includes("highway") || id.includes("motorway") || id.includes("trunk");
        const isMajor = id.includes("primary") || id.includes("secondary") || id.includes("tertiary") || id.includes("major");
        const color = isHighway ? THEME.roadHighway : isMajor ? THEME.roadMajor : THEME.roadMinor;
        map.setPaintProperty(id, "line-color", color);
        continue;
      }

      // --- Fill fallback (remaining fills become land tone) ---
      if (type === "fill") {
        map.setPaintProperty(id, "fill-color", THEME.land);
        continue;
      }

      // --- Labels ---
      if (type === "symbol") {
        const isWater = id.includes("water") || id.includes("ocean") || id.includes("sea") || id.includes("lake") || sl === "water_name";
        const isPrimary = id.includes("country") || id.includes("continent") || id.includes("state") || id.includes("capital") || id.includes("city");

        const textColor = isWater
          ? THEME.labelWater
          : isPrimary
            ? THEME.labelPrimary
            : THEME.labelSecondary;

        map.setPaintProperty(id, "text-color", textColor);
        map.setPaintProperty(id, "text-halo-color", THEME.labelHalo);
        map.setPaintProperty(id, "text-halo-width", 1.5);

        // Icon tinting for POI icons etc
        try {
          map.setPaintProperty(id, "icon-color", THEME.labelSecondary);
          map.setPaintProperty(id, "icon-opacity", 0.6);
        } catch (_) { /* not all symbols have icons */ }

        continue;
      }

    } catch (err) {
      // Silently skip layers that don't support the property
    }
  }
}
