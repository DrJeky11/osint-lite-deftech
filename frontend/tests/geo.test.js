import test from "node:test";
import assert from "node:assert/strict";

import { inferGeo } from "../src/lib/geo.js";

test("inferGeo resolves shared city names when country context is present", () => {
  const result = inferGeo({
    title: "Tripoli officials deny coup rumor in Libya",
    rawText: "Convoy movement was reported in Tripoli, Libya, after a night of unrest.",
    author: { profileLocation: "North Africa" },
    placeHints: ["Tripoli", "Libya"]
  });

  assert.equal(result.locationId, "tripoli-ly");
  assert.equal(result.resolution, "city");
  assert.ok(result.confidence >= 0.7);
});

test("inferGeo rolls ambiguous place names up when profile location is weak", () => {
  const result = inferGeo({
    title: "Rumors spread overnight in Tripoli",
    rawText: "Posts mention unusual movement near government sites in Tripoli.",
    author: { profileLocation: "Tripoli" },
    placeHints: []
  });

  assert.equal(result.resolution, "country");
  assert.ok(result.confidence <= 0.6);
});
