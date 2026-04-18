import test from "node:test";
import assert from "node:assert/strict";

import { buildSignalEvent, computeLocationScores } from "../src/lib/scoring.js";

test("computeLocationScores prefers corroborated hotspots over single-source spikes", () => {
  const referenceTime = "2026-04-17T20:00:00Z";
  const corroborated = [
    buildSignalEvent(
      { id: "one", sourceFamily: "news", source: "Desk", title: "Protest in Quetta", rawText: "", publishedAt: "2026-04-17T18:00:00Z" },
      { name: "Quetta", country: "Pakistan", lat: 30.1798, lon: 66.975, resolution: "city", confidence: 0.82 },
      { severity: 3.8, civilWeight: 2.2, militaryWeight: 1.6, drivers: ["protest activity"], confidencePenalty: 0 },
      3
    ),
    buildSignalEvent(
      { id: "two", sourceFamily: "x", source: "X", title: "Convoy in Quetta", rawText: "", publishedAt: "2026-04-17T17:30:00Z" },
      { name: "Quetta", country: "Pakistan", lat: 30.1798, lon: 66.975, resolution: "city", confidence: 0.76 },
      { severity: 3.6, civilWeight: 1.8, militaryWeight: 1.9, drivers: ["force movement"], confidencePenalty: 0 },
      3
    )
  ];

  const noisySpike = [
    buildSignalEvent(
      { id: "three", sourceFamily: "x", source: "X", title: "Viral chatter", rawText: "", publishedAt: "2026-04-17T19:00:00Z" },
      { name: "Caracas", country: "Venezuela", lat: 10.4806, lon: -66.9036, resolution: "city", confidence: 0.45 },
      { severity: 4.2, civilWeight: 2.5, militaryWeight: 0.4, drivers: ["acceleration in discussion volume"], confidencePenalty: 0.35 },
      1
    )
  ];

  const scores = computeLocationScores([...corroborated, ...noisySpike], { referenceTime });

  assert.equal(scores[0].name, "Quetta");
  assert.ok(scores[0].heat > scores[1].heat);
});
