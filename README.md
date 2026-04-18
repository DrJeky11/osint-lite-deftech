# Signal Atlas

Signal Atlas is a hackathon demo for a global OSINT instability watchfloor. It ingests open RSS reporting, extracts instability-related signals, geolocates them with confidence scoring, and turns them into an interactive heatmap that helps analysts see where civil unrest or military instability may be intensifying.

## What this tool does

- Pulls live RSS items from a curated catalog of international news, analysis, and official sources
- Pulls public Bluesky posts from targeted instability watch queries using the public AppView API
- Normalizes each item into a shared `SourceItem` shape with provenance and feed metadata
- Infers likely geography from article text and source hints, then rolls low-confidence results up to country level
- Classifies signals into civil unrest, military instability, and narrative-risk indicators
- Scores locations based on recency, severity, corroboration, and confidence
- Renders the results as an interactive globe or flat map with evidence bundles and next-step OSINT suggestions

## Current scope

- Data sources: live RSS feeds and public Bluesky watch queries
- Active source mix: international news, official advisories, and conflict-analysis feeds
- Output: a browser-based watchfloor showing hotspots, score splits, evidence, and trend direction
- Current goal: help analysts decide where to focus deeper OSINT next

## How it works

1. `npm run refresh:rss` fetches the live RSS catalog and writes a normalized cache to `src/generated/rss-cache.json`.
2. `npm run refresh:bluesky` collects public Bluesky posts for the watch catalog and writes `src/generated/bluesky-cache.json`.
3. `npm run refresh:live` runs both live refresh steps together.
4. `npm run generate:data` transforms the cached items into signal events and location scores.
5. `npm run build` regenerates the dataset and copies the static app into `dist/`.
6. `npm run dev` serves the app locally so the watchfloor can be viewed in a browser.

## Run locally

```bash
npm run refresh:rss
npm run refresh:bluesky
npm run refresh:live
npm run build
npm run dev
```

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173).

## Scripts

- `npm run refresh:rss` fetches the live RSS catalog and snapshots normalized feed items into `src/generated/rss-cache.json`.
- `npm run refresh:bluesky` fetches public Bluesky watch results into `src/generated/bluesky-cache.json`.
- `npm run refresh:live` refreshes both RSS and BlueSky caches in sequence.
- `npm run generate:data` regenerates the dataset from any live RSS and Bluesky caches when present, otherwise it falls back to seeded demo `SourceItem` records.
- `npm run build` regenerates data and copies the app into `dist/`.
- `npm run build:live` refreshes both live caches, then rebuilds the app.
- `npm test` runs the geolocation, signal-classification, and hotspot-scoring tests.
- `npm run dev` serves the repo locally on port `4173`.

## Current limitations

- Geography is heuristic and backed by a small built-in gazetteer
- Signal classification is still taxonomy and keyword driven
- Bluesky coverage is targeted watch-query collection, not full-network firehose coverage
