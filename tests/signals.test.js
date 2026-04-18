import test from "node:test";
import assert from "node:assert/strict";

import { classifySignal } from "../src/lib/signals.js";

test("classifySignal identifies civil unrest and military stress markers", () => {
  const classification = classifySignal({
    title: "Protest march expands after troop movement",
    rawText: "Residents reported clashes, a convoy, and mutiny rumors after the crackdown."
  });

  assert.equal(classification.signalType, "military");
  assert.ok(classification.civilWeight > 1);
  assert.ok(classification.militaryWeight > 1);
  assert.ok(classification.drivers.includes("force movement"));
});

test("classifySignal suppresses noisy non-instability chatter", () => {
  const classification = classifySignal({
    title: "Celebrity concert near stadium trends after football match",
    rawText: "Fans shared festival clips and celebrity reactions all night."
  });

  assert.equal(classification.signalType, "noise");
  assert.ok(classification.civilWeight < 0.1);
});
