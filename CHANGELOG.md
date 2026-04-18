# Changelog

This file tracks notable project changes with concrete dates.

## 2026-04-18

- Replaced the placeholder repo state with the `Signal Atlas` hackathon demo structure
- Built the browser-based OSINT watchfloor UI with globe and flat-map views, hotspot selection, score splits, evidence bundles, and analyst follow-on actions
- Added core data models and logic for geolocation, signal classification, and location scoring
- Added generated dataset outputs for source items, signal events, and location scores
- Added a live RSS ingestion pipeline with a curated feed catalog, XML parsing, normalization, and cache generation
- Integrated live RSS data into the dataset build flow with fallback to seeded demo data
- Added parser handling for malformed timestamps and Crisis Group date formatting
- Added automated tests covering geolocation, signal classification, scoring, and RSS parsing/normalization
- Updated the README to describe the tool’s purpose, workflow, and current limitations

### 00:24 EDT

- Added a public BlueSky AppView ingestion path with a targeted watch catalog for monitored instability locations
- Added BlueSky normalization, AT-URI to web URL mapping, and duplicate-post merging across overlapping watch queries
- Added a `refresh:bluesky` script and extended dataset generation to merge live RSS and BlueSky caches into a shared source catalog
- Carried richer source metadata into signal events so evidence cards can link back to original posts and show source attribution
- Added BlueSky-focused automated tests and documented the new BlueSky refresh workflow and collection limits

## 2026-04-17

- Created the initial `README.md` starter file and pushed the first repository commit
