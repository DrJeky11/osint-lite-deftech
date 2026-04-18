import { dataset } from "./generated/osint-data.js";
import {
  LANDMASSES,
  projectEquirectangular,
  projectOrthographic
} from "./lib/geo.js";
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
  sourceSummary: document.querySelector(".topbar-meta .muted"),
  detailName: document.getElementById("detail-name"),
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
  sparkline: document.getElementById("sparkline")
};

const state = {
  projection: "globe",
  sourceFamily: "all",
  emphasis: "blend",
  timeWindowHours: 24,
  confidenceFloor: 0.5,
  rotation: { lon: -12, lat: -12 },
  zoom: 1,
  selectedLocationId: null
};

let visibleScores = [];
let hitTargets = [];
let isDragging = false;
let dragOrigin = null;

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function unique(values) {
  return [...new Set(values)];
}

function formatHoursAgo(timestamp) {
  const hours = Math.round((new Date(dataset.generatedAt).getTime() - new Date(timestamp).getTime()) / 36e5);
  return `${hours}h ago`;
}

function heatColor(heat, alpha = 1) {
  const hue = Math.max(0, 188 - heat * 1.55);
  const lightness = 34 + heat * 0.22;
  return `hsla(${hue}, 92%, ${lightness}%, ${alpha})`;
}

function selectedLabel(score) {
  if (!score) {
    return "steady";
  }
  return score.trend;
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

function drawLandPolygon(points, projector, width, height, radius) {
  const projected = points
    .map(([lon, lat]) => projector(lon, lat, width, height, radius))
    .filter((point) => point.visible);

  if (projected.length < 2) {
    return;
  }

  context.beginPath();
  projected.forEach((point, index) => {
    const x = point.x + width / 2;
    const y = point.y + height / 2;
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });
  context.closePath();
  context.fill();
  context.stroke();
}

function drawGraticule(width, height, radius) {
  context.save();
  context.strokeStyle = "rgba(133, 170, 200, 0.14)";
  context.lineWidth = 1;
  const projector = state.projection === "globe"
    ? (lon, lat) => projectOrthographic(lon, lat, state.rotation, radius)
    : (lon, lat) => projectEquirectangular(lon, lat, width, height);

  for (let longitude = -150; longitude <= 180; longitude += 30) {
    context.beginPath();
    let started = false;
    for (let latitude = -75; latitude <= 75; latitude += 5) {
      const point = projector(longitude, latitude);
      if (!point.visible) {
        continue;
      }
      const x = point.x + width / 2;
      const y = point.y + height / 2;
      if (!started) {
        context.moveTo(x, y);
        started = true;
      } else {
        context.lineTo(x, y);
      }
    }
    context.stroke();
  }

  for (let latitude = -60; latitude <= 60; latitude += 30) {
    context.beginPath();
    let started = false;
    for (let longitude = -180; longitude <= 180; longitude += 5) {
      const point = projector(longitude, latitude);
      if (!point.visible) {
        continue;
      }
      const x = point.x + width / 2;
      const y = point.y + height / 2;
      if (!started) {
        context.moveTo(x, y);
        started = true;
      } else {
        context.lineTo(x, y);
      }
    }
    context.stroke();
  }

  context.restore();
}

function drawMap() {
  const { width, height } = resizeCanvas();
  const radius = Math.min(width, height) * 0.34 * state.zoom;
  const gradient = context.createLinearGradient(0, 0, width, height);
  gradient.addColorStop(0, "#07131f");
  gradient.addColorStop(0.55, "#081e32");
  gradient.addColorStop(1, "#030811");
  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);

  context.save();
  context.translate(width / 2, height / 2);
  if (state.projection === "globe") {
    context.beginPath();
    context.arc(0, 0, radius, 0, Math.PI * 2);
    context.fillStyle = "rgba(7, 29, 46, 0.88)";
    context.shadowColor = "rgba(20, 175, 255, 0.2)";
    context.shadowBlur = 24;
    context.fill();
    context.restore();
    drawGraticule(width, height, radius);
    context.save();
    context.translate(width / 2, height / 2);
    context.strokeStyle = "rgba(181, 227, 255, 0.18)";
    context.fillStyle = "rgba(82, 126, 108, 0.54)";
    context.lineWidth = 1.2;
    LANDMASSES.forEach((mass) => {
      drawLandPolygon(
        mass.points,
        (lon, lat) => projectOrthographic(lon, lat, state.rotation, radius),
        width,
        height,
        radius
      );
    });
    context.restore();
  } else {
    context.restore();
    drawGraticule(width, height, radius);
    context.save();
    context.strokeStyle = "rgba(181, 227, 255, 0.16)";
    context.fillStyle = "rgba(65, 120, 104, 0.48)";
    context.lineWidth = 1.1;
    LANDMASSES.forEach((mass) => {
      drawLandPolygon(
        mass.points,
        (lon, lat) => {
          const point = projectEquirectangular(lon, lat, width, height);
          return {
            ...point,
            x: point.x - width / 2,
            y: point.y - height / 2
          };
        },
        width,
        height,
        radius
      );
    });
    context.restore();
  }

  drawHotspots(width, height, radius);
}

function drawHotspots(width, height, radius) {
  hitTargets = [];
  const nowPulse = 0.75 + Math.sin(Date.now() / 380) * 0.12;
  const projector = state.projection === "globe"
    ? (lon, lat) => projectOrthographic(lon, lat, state.rotation, radius)
    : (lon, lat) => {
        const point = projectEquirectangular(lon, lat, width, height);
        return {
          ...point,
          x: point.x - width / 2,
          y: point.y - height / 2
        };
      };

  context.save();
  context.translate(width / 2, height / 2);
  visibleScores.forEach((score) => {
    const point = projector(score.center.lon, score.center.lat);
    if (!point.visible) {
      return;
    }

    const selected = score.id === state.selectedLocationId;
    const radiusPx = 8 + score.heat * 0.19;
    const x = point.x;
    const y = point.y;

    context.beginPath();
    context.arc(x, y, radiusPx * 1.8 * nowPulse, 0, Math.PI * 2);
    context.fillStyle = heatColor(score.heat, 0.12);
    context.fill();

    context.beginPath();
    context.arc(x, y, radiusPx, 0, Math.PI * 2);
    context.fillStyle = heatColor(score.heat, selected ? 0.95 : 0.8);
    context.shadowColor = heatColor(score.heat, 0.65);
    context.shadowBlur = selected ? 24 : 18;
    context.fill();

    context.beginPath();
    context.arc(x, y, Math.max(4, radiusPx * 0.35), 0, Math.PI * 2);
    context.fillStyle = "rgba(246, 251, 255, 0.95)";
    context.shadowBlur = 0;
    context.fill();

    if (selected) {
      context.strokeStyle = "rgba(255,255,255,0.9)";
      context.lineWidth = 1.5;
      context.beginPath();
      context.arc(x, y, radiusPx + 6, 0, Math.PI * 2);
      context.stroke();
    }

    hitTargets.push({
      id: score.id,
      x: x + width / 2,
      y: y + height / 2,
      radius: radiusPx + 8
    });
  });
  context.restore();
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { width: rect.width, height: rect.height };
}

function renderHotspotList() {
  ui.hotspotList.innerHTML = "";

  visibleScores.slice(0, 6).forEach((score) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `hotspot-chip${score.id === state.selectedLocationId ? " is-active" : ""}`;
    button.innerHTML = `
      <span class="chip-name">${score.name}</span>
      <span class="chip-meta">${score.heat.toFixed(0)} heat · ${score.trend}</span>
    `;
    button.addEventListener("click", () => {
      state.selectedLocationId = score.id;
      render();
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
  const points = history.map((value, index) => {
    const x = index * (240 / Math.max(history.length - 1, 1));
    const y = 68 - (value / maxValue) * 56;
    return `${x},${y}`;
  });

  ui.sparkline.innerHTML = `
    <polyline
      fill="none"
      stroke="rgba(255, 188, 92, 0.95)"
      stroke-width="3"
      points="${points.join(" ")}"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  `;
}

function recommendedActions(score) {
  const actions = [];

  if (score.militaryComponent > score.civilComponent) {
    actions.push("Review recent reporting on force posture, officer churn, and command changes in nearby garrisons.");
    actions.push("Cross-check convoy and deployment mentions against satellite, NOTAM, or local transport disruptions.");
  } else {
    actions.push("Expand collection on protest organizers, strike calls, and security-force response in adjacent districts.");
    actions.push("Look for linked local radio, civic channels, and municipal feeds to confirm whether unrest is spreading.");
  }

  if (score.sourceBreakdown.includes("x") || score.sourceBreakdown.includes("bluesky")) {
    actions.push("Sample high-velocity social accounts for coordination patterns and repeated narrative frames.");
  }

  return actions.slice(0, 3);
}

function renderDetails() {
  const score = getSelectedScore();

  if (!score) {
    return;
  }

  ui.detailName.textContent = score.name;
  ui.trendPill.textContent = selectedLabel(score);
  ui.trendPill.dataset.trend = score.trend;
  ui.detailHeat.textContent = score.heat.toFixed(0);
  ui.detailDelta.textContent = `${score.delta > 0 ? "+" : ""}${score.delta.toFixed(0)}`;
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

function render() {
  recomputeVisibleScores();
  drawMap();
  renderHotspotList();
  renderDetails();
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
}

function attachListeners() {
  controls.projection.addEventListener("change", (event) => {
    state.projection = event.target.value;
    render();
  });
  controls.timeWindow.addEventListener("change", (event) => {
    state.timeWindowHours = Number(event.target.value);
    render();
  });
  controls.sourceFamily.addEventListener("change", (event) => {
    state.sourceFamily = event.target.value;
    render();
  });
  controls.emphasis.addEventListener("change", (event) => {
    state.emphasis = event.target.value;
    render();
  });
  controls.confidence.addEventListener("input", (event) => {
    state.confidenceFloor = Number(event.target.value) / 100;
    render();
  });

  canvas.addEventListener("pointerdown", (event) => {
    isDragging = true;
    dragOrigin = {
      x: event.clientX,
      y: event.clientY,
      lon: state.rotation.lon,
      lat: state.rotation.lat
    };
  });

  canvas.addEventListener("pointermove", (event) => {
    if (!isDragging || state.projection !== "globe") {
      return;
    }
    const deltaX = event.clientX - dragOrigin.x;
    const deltaY = event.clientY - dragOrigin.y;
    state.rotation.lon = dragOrigin.lon + deltaX * 0.4;
    state.rotation.lat = clamp(dragOrigin.lat + deltaY * 0.25, -65, 65);
    drawMap();
  });

  canvas.addEventListener("pointerup", (event) => {
    if (isDragging && Math.abs(event.clientX - dragOrigin.x) < 5 && Math.abs(event.clientY - dragOrigin.y) < 5) {
      const rect = canvas.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const clickY = event.clientY - rect.top;
      const hit = hitTargets.find((target) => {
        return Math.hypot(target.x - clickX, target.y - clickY) <= target.radius;
      });

      if (hit) {
        state.selectedLocationId = hit.id;
        render();
      }
    }

    isDragging = false;
    dragOrigin = null;
  });

  canvas.addEventListener("pointerleave", () => {
    isDragging = false;
    dragOrigin = null;
  });

  canvas.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      state.zoom = clamp(state.zoom - event.deltaY * 0.0012, 0.85, 1.45);
      drawMap();
    },
    { passive: false }
  );

  window.addEventListener("resize", render);
}

function init() {
  ui.lastUpdated.textContent = `Snapshot ${new Date(dataset.generatedAt).toLocaleString()}`;
  const sourceCatalog = dataset.sourceCatalog?.length ? dataset.sourceCatalog : dataset.feedCatalog ?? [];
  if (sourceCatalog.length) {
    const sources = unique(sourceCatalog.map((entry) => entry.source));
    let summary = `${sources.slice(0, 4).join(" + ")} · ${sourceCatalog.length} live sources`;
    if (dataset.sourceStatus?.bluesky !== "loaded") {
      summary += " · BlueSky cache missing";
    }
    ui.sourceSummary.textContent = summary;
  } else if (dataset.failures?.length) {
    ui.sourceSummary.textContent = "Live refresh failed, showing demo cache";
  } else if (dataset.sourceStatus?.bluesky !== "loaded") {
    ui.sourceSummary.textContent = "BlueSky cache missing, showing available sources only";
  }
  syncControls();
  attachListeners();
  render();
}

init();
