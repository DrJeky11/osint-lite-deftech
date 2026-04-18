# Scrapers

This is a list of python programs with FASTapi wrappers to act as backend scripts for collecting and analayzing OSINT sources.  

- `news/`: fetches articles and summarizes them.
- `bluesky/`: searches Bluesky posts and summarizes them.
- `x/`: searches X posts through the official recent-search API and summarizes them.
  Requires `X_BEARER_TOKEN` in [scrapers/x/.env](C:/Users/zeetw/Documents/GitHub/osint-lite-deftech/scrapers/x/.env).
  X recent search is limited to roughly the last 7 days unless the API access level is upgraded.
