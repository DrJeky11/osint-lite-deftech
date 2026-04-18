import { dataset } from "./generated/osint-data.js";
import { LANDMASSES, projectEquirectangular } from "./lib/geo.js";
import { computeLocationScores } from "./lib/scoring.js";

const canvas = document.getElementById("map-canvas");
const context = canvas.getContext("2d");

const controls = {
  projection: document.getElementById("projection-select"),
  timeWindow: document.getElementById("time-window-select"),
  sourceFamily: document.getElementById("source-family-select"),
  emphasis: document.getElementById("emphasis-select"),
  confidence: document.getElementById("confidence-range")
};

const ui = {
  hotspotList: document.getElementById("hotspot-list"),
  lastUpdated: document.getElementById("last-updated"),
  sourceSummary: document.getElementById("source-summary"),
  detailName: document.getElementById("detail-name"),
  detailBrief: document.getElementById("detail-brief"),
  trendPill: document.getElementById("trend-pill"),
  detailHeat: document.getElementById("detail-heat"),
  detailDelta: document.getElementById("detail-delta"),
  detailConfidence: document.getElementById("detail-confidence"),
  civilScore: document.getElementById("civil-score"),
  militaryScore: document.getElementById("military-score"),
  civilMeter: document.getElementById("civil-meter"),
  militaryMeter: document.getElementById("military-meter"),
  driverList: document.getElementById("driver-list"),
  evidenceList: document.getElementById("evidence-list"),
  actionList: document.getElementById("action-list"),
  sparkline: document.getElementById("sparkline"),
  confidenceOutput: document.getElementById("confidence-output"),
  metricHotspots: document.getElementById("metric-hotspots"),
  metricSignals: document.getElementById("metric-signals"),
  metricSources: document.getElementById("metric-sources"),
  metricWindow: document.getElementById("metric-window")
};

const LIGHT_DIRECTION = normalizeVector({ x: -0.58, y: -0.24, z: 0.78 });
const STAR_FIELD = buildStarField(140);
const LAND_DOTS = buildLandDots(LANDMASSES, 3.5);

const state = {
  projection: "globe",
  sourceFamily: "all",
  emphasis: "blend",
  timeWindowHours: 24,
  confidenceFloor: 0.5,
  rotation: { lon: -22, lat: -10 },
  zoom: 1,
  selectedLocationId: null
};

let visibleScores = [];
let hitTargets = [];
let isDragging = false;
let dragOrigin = null;
let needsUiRefresh = true;
let previousFrame = 0;

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function normalizeVector(vector) {
  const magnitude = Math.hypot(vector.x, vector.y, vector.z) || 1;
  return {
    x: vector.x / magnitude,
    y: vector.y / magnitude,
    z: vector.z / magnitude
  };
}

function wrapAngle(value) {
  return ((value + 180) % 360 + 360) % 360 - 180;
}

function fract(value) {
  return value - Math.floor(value);
}

function formatHoursAgo(timestamp) {
  const hours = Math.round(
    (new Date(dataset.generatedAt).getTime() - new Date(timestamp).getTime()) / 36e5
  );
  return `${hours}h ago`;
}

function formatDelta(delta) {
  return `${delta > 0 ? "+" : ""}${delta.toFixed(0)}`;
}

function heatColor(heat, alpha = 1) {
  const hue = Math.max(0, 188 - heat * 1.5);
  const lightness = 36 + heat * 0.2;
  return `hsla(${hue}, 94%, ${lightness}%, ${alpha})`;
}

function selectedLabel(score) {
  return score ? score.trend : "steady";
}

function pointInPolygon(lon, lat, polygon) {
  let inside = false;

  for (let index = 0, previous = polygon.length - 1; index < polygon.length; previous = index, index += 1) {
    const [x1, y1] = polygon[index];
    const [x2, y2] = polygon[previous];
    const crosses =
      y1 > lat !== y2 > lat &&
      lon < ((x2 - x1) * (lat - y1)) / ((y2 - y1) || Number.EPSILON) + x1;

    if (crosses) {
      inside = !inside;
    }
  }

  return inside;
}

function buildLandDots(masses, step) {
  const dots = [];

  masses.forEach((mass, massIndex) => {
    const longitudes = mass.points.map(([lon]) => lon);
    const latitudes = mass.points.map(([, lat]) => lat);
    const minLon = Math.min(...longitudes);
    const maxLon = Math.max(...longitudes);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);

    for (let lat = minLat; lat <= maxLat; lat += step) {
      const rowIndex = Math.round((lat - minLat) / step);
      const rowOffset = rowIndex % 2 === 0 ? 0 : step / 2;

      for (let lon = minLon + rowOffset; lon <= maxLon; lon += step) {
        const jitterLon =
          lon + Math.sin((lon + massIndex * 19) * 0.47 + lat * 0.31) * step * 0.22;
        const jitterLat =
          lat + Math.cos((lat + massIndex * 13) * 0.41 + lon * 0.27) * step * 0.18;

        if (pointInPolygon(jitterLon, jitterLat, mass.points)) {
          dots.push({ lon: jitterLon, lat: jitterLat });
        }
      }
    }
  });

  return dots;
}

function buildStarField(count) {
  return Array.from({ length: count }, (_, index) => {
    const seed = index + 1;
    return {
      x: fract(Math.sin(seed * 12.9898) * 43758.5453),
      y: fract(Math.sin(seed * 78.233) * 12741.9281),
      size: 0.5 + fract(Math.sin(seed * 34.123) * 9123.55) * 2.2,
      alpha: 0.16 + fract(Math.sin(seed * 22.713) * 3214.18) * 0.44,
      speed: 0.0005 + fract(Math.sin(seed * 4.113) * 687.31) * 0.0015,
      phase: fract(Math.sin(seed * 91.73) * 9812.51) * Math.PI * 2
    };
  });
}

function getFilteredSignalEvents() {
  return dataset.signalEvents.filter((event) => {
    const ageHours = (new Date(dataset.generatedAt).getTime() - new Date(event.timestamp).getTime()) / 36e5;
    const withinWindow = ageHours <= state.timeWindowHours;
    const matchesSource = state.sourceFamily === "all" || event.sourceFamily === state.sourceFamily;
    const matchesConfidence = event.geo.confidence >= state.confidenceFloor;
    return withinWindow && matchesSource && matchesConfidence;
  });
}

function recomputeVisibleScores() {
  visibleScores = computeLocationScores(getFilteredSignalEvents(), {
    referenceTime: dataset.generatedAt,
    emphasis: state.emphasis
  }).filter((score) => score.confidence >= state.confidenceFloor);

  if (!visibleScores.length) {
    state.selectedLocationId = null;
    return;
  }

  const selectedStillVisible = visibleScores.some((score) => score.id === state.selectedLocationId);
  if (!selectedStillVisible) {
    state.selectedLocationId = visibleScores[0].id;
  }
}

function getSelectedScore() {
  return visibleScores.find((score) => score.id === state.selectedLocationId) ?? visibleScores[0] ?? null;
}

function getGlobeVector(lon, lat) {
  const lambda = ((lon + state.rotation.lon) * Math.PI) / 180;
  const phi = (lat * Math.PI) / 180;
  const phi0 = (state.rotation.lat * Math.PI) / 180;

  return {
    x: Math.cos(phi) * Math.sin(lambda),
    y: Math.cos(phi0) * Math.sin(phi) - Math.sin(phi0) * Math.cos(phi) * Math.cos(lambda),
    z: Math.sin(phi0) * Math.sin(phi) + Math.cos(phi0) * Math.cos(phi) * Math.cos(lambda)
  };
}

function projectGlobePoint(lon, lat, radius) {
  const vector = getGlobeVector(lon, lat);

  return {
    x: vector.x * radius,
    y: vector.y * radius,
    visible: vector.z > 0,
    depth: vector.z,
    light: clamp(
      vector.x * LIGHT_DIRECTION.x + vector.y * LIGHT_DIRECTION.y + vector.z * LIGHT_DIRECTION.z,
      -1,
      1
    )
  };
}

function projectFlatPoint(lon, lat, width, height) {
  const paddingX = width * 0.08;
  const paddingY = height * 0.12;
  const point = projectEquirectangular(lon, lat, width - paddingX * 2, height - paddingY * 2);

  return {
    x: point.x + paddingX - width / 2,
    y: point.y + paddingY - height / 2,
    visible: true,
    depth: 1,
    light: 0.45
  };
}

function createProjector(width, height, radius) {
  if (state.projection === "globe") {
    return (lon, lat) => projectGlobePoint(lon, lat, radius);
  }

  return (lon, lat) => projectFlatPoint(lon, lat, width, height);
}

function drawRoundedRect(x, y, width, height, radius) {
  const safeRadius = Math.min(radius, width / 2, height / 2);
  context.beginPath();
  context.moveTo(x + safeRadius, y);
  context.lineTo(x + width - safeRadius, y);
  context.quadraticCurveTo(x + width, y, x + width, y + safeRadius);
  context.lineTo(x + width, y + height - safeRadius);
  context.quadraticCurveTo(x + width, y + height, x + width - safeRadius, y + height);
  context.lineTo(x + safeRadius, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - safeRadius);
  context.lineTo(x, y + safeRadius);
  context.quadraticCurveTo(x, y, x + safeRadius, y);
  context.closePath();
}

function drawLandPolygon(points, projector) {
  const projected = points.map(([lon, lat]) => projector(lon, lat)).filter((point) => point.visible);

  if (projected.length < 2) {
    return;
  }

  context.beginPath();
  projected.forEach((point, index) => {
    if (index === 0) {
      context.moveTo(point.x, point.y);
    } else {
      context.lineTo(point.x, point.y);
    }
  });
  context.closePath();
  context.fill();
  context.stroke();
}

function drawGraticule(width, height, radius, projector) {
  context.save();
  context.translate(width / 2, height / 2);
  context.strokeStyle = state.projection === "globe" ? "rgba(140, 186, 224, 0.12)" : "rgba(120, 165, 204, 0.18)";
  context.lineWidth = 1;

  for (let longitude = -150; longitude <= 180; longitude += 30) {
    context.beginPath();
    let started = false;

    for (let latitude = -75; latitude <= 75; latitude += 4) {
      const point = projector(longitude, latitude);
      if (!point.visible) {
        continue;
      }

      if (!started) {
        context.moveTo(point.x, point.y);
        started = true;
      } else {
        context.lineTo(point.x, point.y);
      }
    }

    context.stroke();
  }

  for (let latitude = -60; latitude <= 60; latitude += 30) {
    context.beginPath();
    let started = false;

    for (let longitude = -180; longitude <= 180; longitude += 4) {
      const point = projector(longitude, latitude);
      if (!point.visible) {
        continue;
      }

      if (!started) {
        context.moveTo(point.x, point.y);
        started = true;
      } else {
        context.lineTo(point.x, point.y);
      }
    }

    context.stroke();
  }

  context.restore();
}

function drawLandMasses(width, height, projector) {
  context.save();
  context.translate(width / 2, height / 2);
  context.fillStyle = state.projection === "globe" ? "rgba(12, 56, 71, 0.42)" : "rgba(18, 64, 79, 0.38)";
  context.strokeStyle = state.projection === "globe" ? "rgba(147, 245, 217, 0.12)" : "rgba(147, 245, 217, 0.14)";
  context.lineWidth = 1.1;

  if (state.projection !== "globe") {
    LANDMASSES.forEach((mass) => {
      drawLandPolygon(mass.points, projector);
    });
  }

  LAND_DOTS.forEach((dot) => {
    const point = projector(dot.lon, dot.lat);
    if (!point.visible) {
      return;
    }

    const intensity = state.projection === "globe" ? clamp((point.light + 1) / 2, 0.15, 1) : 0.65;
    const alpha = 0.2 + intensity * 0.5;
    const size = state.projection === "globe" ? 0.9 + point.depth * 0.8 : 1.1;

    context.beginPath();
    context.arc(point.x, point.y, size, 0, Math.PI * 2);
    context.fillStyle = `rgba(147, 255, 231, ${alpha})`;
    context.fill();
  });

  context.restore();
}

function drawBackground(width, height, timestamp) {
  const gradient = context.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#06111d");
  gradient.addColorStop(0.42, "#081528");
  gradient.addColorStop(1, "#02060d");

  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);

  STAR_FIELD.forEach((star) => {
    const twinkle = 0.45 + Math.sin(timestamp * star.speed + star.phase) * 0.4;
    context.beginPath();
    context.arc(star.x * width, star.y * height, star.size, 0, Math.PI * 2);
    context.fillStyle = `rgba(230, 241, 255, ${star.alpha * twinkle})`;
    context.fill();
  });

  context.strokeStyle = "rgba(120, 214, 255, 0.06)";
  context.lineWidth = 1;
  context.beginPath();
  context.ellipse(width * 0.5, height * 0.48, width * 0.37, height * 0.3, 0, 0, Math.PI * 2);
  context.stroke();
}

function drawGlobe(width, height, radius) {
  const centerX = width / 2;
  const centerY = height / 2;

  const halo = context.createRadialGradient(centerX, centerY, radius * 0.9, centerX, centerY, radius * 1.52);
  halo.addColorStop(0, "rgba(0, 0, 0, 0)");
  halo.addColorStop(0.68, "rgba(109, 220, 255, 0.08)");
  halo.addColorStop(1, "rgba(109, 220, 255, 0)");
  context.fillStyle = halo;
  context.beginPath();
  context.arc(centerX, centerY, radius * 1.52, 0, Math.PI * 2);
  context.fill();

  context.save();
  context.beginPath();
  context.arc(centerX, centerY, radius, 0, Math.PI * 2);
  context.clip();

  const ocean = context.createRadialGradient(
    centerX + LIGHT_DIRECTION.x * radius * 0.58,
    centerY + LIGHT_DIRECTION.y * radius * 0.58,
    radius * 0.12,
    centerX,
    centerY,
    radius * 1.15
  );
  ocean.addColorStop(0, "#3db0e1");
  ocean.addColorStop(0.28, "#12628c");
  ocean.addColorStop(0.64, "#0a2941");
  ocean.addColorStop(1, "#06111a");
  context.fillStyle = ocean;
  context.fillRect(centerX - radius, centerY - radius, radius * 2, radius * 2);

  const shadow = context.createRadialGradient(
    centerX - LIGHT_DIRECTION.x * radius * 0.66,
    centerY - LIGHT_DIRECTION.y * radius * 0.66,
    radius * 0.14,
    centerX,
    centerY,
    radius * 1.24
  );
  shadow.addColorStop(0, "rgba(1, 4, 9, 0.02)");
  shadow.addColorStop(0.56, "rgba(2, 8, 15, 0.18)");
  shadow.addColorStop(1, "rgba(1, 4, 10, 0.88)");
  context.fillStyle = shadow;
  context.fillRect(centerX - radius, centerY - radius, radius * 2, radius * 2);

  for (let y = centerY - radius; y <= centerY + radius; y += 6) {
    context.strokeStyle = "rgba(255, 255, 255, 0.02)";
    context.beginPath();
    context.moveTo(centerX - radius, y);
    context.lineTo(centerX + radius, y);
    context.stroke();
  }

  const projector = createProjector(width, height, radius);
  drawGraticule(width, height, radius, projector);
  drawLandMasses(width, height, projector);

  context.restore();

  context.beginPath();
  context.arc(centerX, centerY, radius, 0, Math.PI * 2);
  context.strokeStyle = "rgba(174, 234, 255, 0.24)";
  context.lineWidth = 1.4;
  context.stroke();
}

function drawFlatMap(width, height, radius) {
  const projector = createProjector(width, height, radius);
  drawGraticule(width, height, radius, projector);
  drawLandMasses(width, height, projector);

  context.save();
  context.strokeStyle = "rgba(174, 234, 255, 0.12)";
  context.lineWidth = 1;
  context.strokeRect(width * 0.08, height * 0.12, width * 0.84, height * 0.76);
  context.restore();
}

function drawSelectedLabel(score, x, y) {
  const label = score.name.toUpperCase();
  const subLabel = `${score.heat.toFixed(0)} HEAT  ${selectedLabel(score).toUpperCase()}`;

  context.save();
  context.font = '600 11px "SF Mono", "IBM Plex Mono", monospace';
  const labelWidth = Math.max(context.measureText(label).width, context.measureText(subLabel).width);
  const cardWidth = labelWidth + 24;
  const cardHeight = 44;
  const offsetX = 18;
  const offsetY = -52;

  context.strokeStyle = "rgba(255, 178, 95, 0.7)";
  context.lineWidth = 1.1;
  context.beginPath();
  context.moveTo(x, y);
  context.lineTo(x + offsetX - 6, y + offsetY + cardHeight - 12);
  context.stroke();

  drawRoundedRect(x + offsetX, y + offsetY, cardWidth, cardHeight, 10);
  context.fillStyle = "rgba(4, 9, 16, 0.92)";
  context.fill();
  context.strokeStyle = "rgba(120, 214, 255, 0.28)";
  context.stroke();

  context.fillStyle = "#f5f8ff";
  context.fillText(label, x + offsetX + 12, y + offsetY + 17);
  context.fillStyle = "rgba(170, 190, 210, 0.88)";
  context.fillText(subLabel, x + offsetX + 12, y + offsetY + 33);
  context.restore();
}

function drawHotspots(width, height, radius, timestamp) {
  hitTargets = [];
  const projector = createProjector(width, height, radius);
  const pulse = 0.78 + Math.sin(timestamp / 380) * 0.12;

  context.save();
  context.translate(width / 2, height / 2);

  visibleScores.forEach((score) => {
    const point = projector(score.center.lon, score.center.lat);
    if (!point.visible) {
      return;
    }

    const selected = score.id === state.selectedLocationId;
    const radiusPx = 6 + score.heat * 0.15;
    const x = point.x;
    const y = point.y;
    const alphaBoost = selected ? 1 : 0.82;

    context.beginPath();
    context.arc(x, y, radiusPx * 1.85 * pulse, 0, Math.PI * 2);
    context.fillStyle = heatColor(score.heat, 0.11 * alphaBoost);
    context.fill();

    context.beginPath();
    context.arc(x, y, radiusPx, 0, Math.PI * 2);
    context.fillStyle = heatColor(score.heat, 0.88 * alphaBoost);
    context.shadowColor = heatColor(score.heat, 0.7);
    context.shadowBlur = selected ? 28 : 18;
    context.fill();

    context.beginPath();
    context.arc(x, y, Math.max(3, radiusPx * 0.3), 0, Math.PI * 2);
    context.fillStyle = "rgba(245, 250, 255, 0.96)";
    context.shadowBlur = 0;
    context.fill();

    if (selected) {
      context.strokeStyle = "rgba(255, 255, 255, 0.92)";
      context.lineWidth = 1.35;
      context.beginPath();
      context.arc(x, y, radiusPx + 6, 0, Math.PI * 2);
      context.stroke();
      drawSelectedLabel(score, x, y);
    }

    hitTargets.push({
      id: score.id,
      x: x + width / 2,
      y: y + height / 2,
      radius: radiusPx + 10
    });
  });

  context.restore();
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;

  if (canvas.width !== Math.round(rect.width * ratio) || canvas.height !== Math.round(rect.height * ratio)) {
    canvas.width = Math.round(rect.width * ratio);
    canvas.height = Math.round(rect.height * ratio);
  }

  context.setTransform(ratio, 0, 0, ratio, 0, 0);

  return {
    width: rect.width,
    height: rect.height
  };
}

function drawMap(timestamp) {
  const { width, height } = resizeCanvas();
  const radius = Math.min(width, height) * (state.projection === "globe" ? 0.34 : 0.38) * state.zoom;

  drawBackground(width, height, timestamp);

  if (state.projection === "globe") {
    drawGlobe(width, height, radius);
  } else {
    drawFlatMap(width, height, radius);
  }

  drawHotspots(width, height, radius, timestamp);
}

function renderMetrics() {
  const filteredEvents = getFilteredSignalEvents();
  const sourceCount = unique(
    filteredEvents.map((event) => event.sourceName ?? event.sourceFamily ?? event.source)
  ).length;

  ui.metricHotspots.textContent = `${visibleScores.length}`;
  ui.metricSignals.textContent = `${filteredEvents.length}`;
  ui.metricSources.textContent = `${sourceCount}`;
  ui.metricWindow.textContent = `${state.timeWindowHours}h`;
  ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
}

function renderHotspotList() {
  ui.hotspotList.innerHTML = "";

  if (!visibleScores.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No theaters match the active filters";
    ui.hotspotList.appendChild(empty);
    return;
  }

  visibleScores.slice(0, 6).forEach((score, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `hotspot-chip${score.id === state.selectedLocationId ? " is-active" : ""}`;
    button.innerHTML = `
      <span class="chip-rank">${String(index + 1).padStart(2, "0")} priority</span>
      <span class="chip-name">${score.name}</span>
      <span class="chip-delta">${formatDelta(score.delta)} delta</span>
      <span class="chip-meta">${score.heat.toFixed(0)} heat · ${selectedLabel(score)}</span>
    `;
    button.addEventListener("click", () => {
      state.selectedLocationId = score.id;
      needsUiRefresh = true;
    });
    ui.hotspotList.appendChild(button);
  });
}

function renderSparkline(history) {
  if (!history.length) {
    ui.sparkline.innerHTML = "";
    return;
  }

  const maxValue = Math.max(...history, 1);
  const points = history.map((value, index) => ({
    x: index * (240 / Math.max(history.length - 1, 1)),
    y: 68 - (value / maxValue) * 54
  }));
  const polylinePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = `0,72 ${polylinePoints} 240,72`;
  const lastPoint = points.at(-1);

  ui.sparkline.innerHTML = `
    <defs>
      <linearGradient id="spark-fill" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="rgba(255, 178, 95, 0.42)" />
        <stop offset="100%" stop-color="rgba(255, 178, 95, 0)" />
      </linearGradient>
    </defs>
    <polygon fill="url(#spark-fill)" points="${areaPoints}" />
    <polyline
      fill="none"
      stroke="rgba(255, 178, 95, 0.95)"
      stroke-width="3"
      points="${polylinePoints}"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <circle
      cx="${lastPoint.x}"
      cy="${lastPoint.y}"
      r="4"
      fill="rgba(255, 245, 232, 0.96)"
      stroke="rgba(255, 178, 95, 0.88)"
      stroke-width="2"
    />
  `;
}

function recommendedActions(score) {
  const actions = [];

  if (score.militaryComponent > score.civilComponent) {
    actions.push("Review recent reporting on force posture, officer churn, and command changes in nearby garrisons.");
    actions.push("Cross-check convoy and deployment mentions against satellite, NOTAM, or transport disruption signals.");
  } else {
    actions.push("Expand collection on protest organizers, strike calls, and security-force response in adjacent districts.");
    actions.push("Look for linked local radio, civic channels, and municipal feeds to confirm whether unrest is spreading.");
  }

  if (score.sourceBreakdown.includes("x") || score.sourceBreakdown.includes("bluesky")) {
    actions.push("Sample high-velocity social accounts for coordination patterns and repeated narrative frames.");
  }

  return actions.slice(0, 3);
}

function buildDetailBrief(score) {
  const dominant = score.militaryComponent > score.civilComponent + 8
    ? "Military-led"
    : score.civilComponent > score.militaryComponent + 8
      ? "Civil-led"
      : "Mixed";

  return `${dominant} pressure profile with ${score.evidenceBundle.length} corroborating items in the current ${state.timeWindowHours}h watch window at ${Math.round(score.confidence * 100)}% geo confidence.`;
}

function clearDetails() {
  ui.detailName.textContent = "No active theater";
  ui.detailBrief.textContent = "Adjust the current filters to surface an active location.";
  ui.trendPill.textContent = "steady";
  ui.trendPill.dataset.trend = "steady";
  ui.detailHeat.textContent = "0";
  ui.detailDelta.textContent = "0";
  ui.detailConfidence.textContent = "0%";
  ui.civilScore.textContent = "0";
  ui.militaryScore.textContent = "0";
  ui.civilMeter.style.width = "0%";
  ui.militaryMeter.style.width = "0%";
  ui.driverList.innerHTML = "";
  ui.evidenceList.innerHTML = '<p class="empty-state">No corroborating items for the current filter set</p>';
  ui.actionList.innerHTML = "";
  ui.sparkline.innerHTML = "";
}

function renderDetails() {
  const score = getSelectedScore();

  if (!score) {
    clearDetails();
    return;
  }

  ui.detailName.textContent = score.name;
  ui.detailBrief.textContent = buildDetailBrief(score);
  ui.trendPill.textContent = selectedLabel(score);
  ui.trendPill.dataset.trend = score.trend;
  ui.detailHeat.textContent = score.heat.toFixed(0);
  ui.detailDelta.textContent = formatDelta(score.delta);
  ui.detailConfidence.textContent = `${Math.round(score.confidence * 100)}%`;
  ui.civilScore.textContent = score.civilComponent.toFixed(0);
  ui.militaryScore.textContent = score.militaryComponent.toFixed(0);
  ui.civilMeter.style.width = `${Math.min(100, score.civilComponent)}%`;
  ui.militaryMeter.style.width = `${Math.min(100, score.militaryComponent)}%`;

  renderSparkline(score.history);

  ui.driverList.innerHTML = "";
  score.topDrivers.forEach((driver) => {
    const item = document.createElement("li");
    item.textContent = driver;
    ui.driverList.appendChild(item);
  });

  ui.evidenceList.innerHTML = "";
  score.evidenceBundle.forEach((event) => {
    const card = document.createElement("article");
    card.className = "evidence-item";
    const meta = document.createElement("div");
    meta.className = "evidence-meta";
    const sourceLabel = document.createElement("span");
    sourceLabel.textContent = event.sourceFamily;
    const ageLabel = document.createElement("span");
    ageLabel.textContent = formatHoursAgo(event.timestamp);
    meta.append(sourceLabel, ageLabel);

    const heading = document.createElement("h4");
    if (event.url) {
      const link = document.createElement("a");
      link.href = event.url;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = event.title;
      heading.appendChild(link);
    } else {
      heading.textContent = event.title;
    }

    const body = document.createElement("p");
    body.textContent = event.excerpt;

    const footer = document.createElement("footer");
    const authorName = event.author?.handle ? `@${event.author.handle}` : event.author?.name ?? event.sourceName;
    const geoLabel = document.createElement("span");
    geoLabel.textContent = `${authorName} · ${event.geo.name} · ${Math.round(event.geo.confidence * 100)}% geo confidence`;
    const typeLabel = document.createElement("span");
    typeLabel.textContent = event.classification.signalType;
    footer.append(geoLabel, typeLabel);

    card.append(meta, heading, body, footer);
    ui.evidenceList.appendChild(card);
  });

  ui.actionList.innerHTML = "";
  recommendedActions(score).forEach((action) => {
    const item = document.createElement("li");
    item.textContent = action;
    ui.actionList.appendChild(item);
  });
}

function syncControls() {
  const sourceOptions = [
    { value: "all", label: "All sources" },
    ...unique(dataset.signalEvents.map((event) => event.sourceFamily)).map((family) => ({
      value: family,
      label: family.charAt(0).toUpperCase() + family.slice(1)
    }))
  ];

  controls.sourceFamily.innerHTML = sourceOptions
    .map((option) => `<option value="${option.value}">${option.label}</option>`)
    .join("");

  controls.projection.value = state.projection;
  controls.timeWindow.value = String(state.timeWindowHours);
  controls.sourceFamily.value = state.sourceFamily;
  controls.emphasis.value = state.emphasis;
  controls.confidence.value = String(state.confidenceFloor * 100);
  ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
}

function refreshUi() {
  recomputeVisibleScores();
  renderMetrics();
  renderHotspotList();
  renderDetails();
  needsUiRefresh = false;
}

function attachListeners() {
  controls.projection.addEventListener("change", (event) => {
    state.projection = event.target.value;
    needsUiRefresh = true;
  });

  controls.timeWindow.addEventListener("change", (event) => {
    state.timeWindowHours = Number(event.target.value);
    needsUiRefresh = true;
  });

  controls.sourceFamily.addEventListener("change", (event) => {
    state.sourceFamily = event.target.value;
    needsUiRefresh = true;
  });

  controls.emphasis.addEventListener("change", (event) => {
    state.emphasis = event.target.value;
    needsUiRefresh = true;
  });

  controls.confidence.addEventListener("input", (event) => {
    state.confidenceFloor = Number(event.target.value) / 100;
    ui.confidenceOutput.textContent = `${Math.round(state.confidenceFloor * 100)}%`;
    needsUiRefresh = true;
  });

  canvas.addEventListener("pointerdown", (event) => {
    isDragging = true;
    dragOrigin = {
      x: event.clientX,
      y: event.clientY,
      lon: state.rotation.lon,
      lat: state.rotation.lat
    };
    canvas.setPointerCapture(event.pointerId);
  });

  canvas.addEventListener("pointermove", (event) => {
    if (isDragging && state.projection === "globe") {
      const deltaX = event.clientX - dragOrigin.x;
      const deltaY = event.clientY - dragOrigin.y;
      state.rotation.lon = wrapAngle(dragOrigin.lon + deltaX * 0.38);
      state.rotation.lat = clamp(dragOrigin.lat + deltaY * 0.22, -65, 65);
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const hoverX = event.clientX - rect.left;
    const hoverY = event.clientY - rect.top;
    const hit = hitTargets.find((target) => Math.hypot(target.x - hoverX, target.y - hoverY) <= target.radius);

    canvas.style.cursor = hit ? "pointer" : state.projection === "globe" ? "grab" : "default";
  });

  canvas.addEventListener("pointerup", (event) => {
    const moved = dragOrigin
      ? Math.hypot(event.clientX - dragOrigin.x, event.clientY - dragOrigin.y)
      : Number.POSITIVE_INFINITY;

    if (dragOrigin && moved < 6) {
      const rect = canvas.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const clickY = event.clientY - rect.top;
      const hit = hitTargets.find((target) => Math.hypot(target.x - clickX, target.y - clickY) <= target.radius);

      if (hit) {
        state.selectedLocationId = hit.id;
        needsUiRefresh = true;
      }
    }

    if (canvas.hasPointerCapture(event.pointerId)) {
      canvas.releasePointerCapture(event.pointerId);
    }

    isDragging = false;
    dragOrigin = null;
    canvas.style.cursor = state.projection === "globe" ? "grab" : "default";
  });

  canvas.addEventListener("pointercancel", () => {
    isDragging = false;
    dragOrigin = null;
  });

  canvas.addEventListener("pointerleave", () => {
    if (!isDragging) {
      canvas.style.cursor = state.projection === "globe" ? "grab" : "default";
    }
  });

  canvas.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      state.zoom = clamp(state.zoom - event.deltaY * 0.0011, 0.82, 1.42);
    },
    { passive: false }
  );

  window.addEventListener("resize", () => {
    needsUiRefresh = true;
  });
}

function animate(timestamp) {
  if (needsUiRefresh) {
    refreshUi();
  }

  const deltaSeconds = previousFrame ? (timestamp - previousFrame) / 1000 : 0;
  previousFrame = timestamp;

  if (state.projection === "globe" && !isDragging) {
    state.rotation.lon = wrapAngle(state.rotation.lon + deltaSeconds * 3.1);
  }

  drawMap(timestamp);
  window.requestAnimationFrame(animate);
}

function init() {
  ui.lastUpdated.textContent = `Snapshot ${new Date(dataset.generatedAt).toLocaleString()}`;

  const sourceCatalog = dataset.sourceCatalog?.length ? dataset.sourceCatalog : dataset.feedCatalog ?? [];
  if (sourceCatalog.length) {
    const sources = unique(sourceCatalog.map((entry) => entry.source));
    let summary = `${sources.slice(0, 4).join(" + ")} · ${sourceCatalog.length} live feeds`;
    if (dataset.sourceStatus?.bluesky !== "loaded") {
      summary += " · Bluesky cache missing";
    }
    ui.sourceSummary.textContent = summary;
  } else if (dataset.failures?.length) {
    ui.sourceSummary.textContent = "Live refresh failed, showing demo cache";
  } else if (dataset.sourceStatus?.bluesky !== "loaded") {
    ui.sourceSummary.textContent = "Bluesky cache missing, showing available sources only";
  }

  syncControls();
  attachListeners();
  refreshUi();
  window.requestAnimationFrame(animate);
}

init();
