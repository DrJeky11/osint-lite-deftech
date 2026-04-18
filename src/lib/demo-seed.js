export const BASE_TIME = "2026-04-17T20:00:00Z";

export const SOURCE_ITEMS = [
  {
    id: "khartoum-news-1",
    sourceFamily: "news",
    source: "Nile Desk",
    title: "Shelling reported near logistics depots as residents flee southern Khartoum",
    rawText:
      "Residents in Khartoum reported renewed shelling near logistics depots overnight, with roadblocks, outages, and small protest gatherings after army and RSF positions shifted.",
    language: "en",
    url: "https://example.com/khartoum-1",
    author: { name: "Nile Desk", profileLocation: "Khartoum" },
    engagement: { shares: 120, comments: 40 },
    placeHints: ["Khartoum", "Sudan"],
    provenance: "public news report",
    hoursAgo: 2
  },
  {
    id: "khartoum-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "Checkpoint lines getting longer around Khartoum after troop movement reports",
    rawText:
      "Witnesses say convoy traffic increased before dawn in Khartoum and nearby districts. Posts mention troop movement, checkpoints, and fears of another crackdown.",
    language: "en",
    url: "https://x.example.com/khartoum-1",
    author: { name: "OpenSignals", profileLocation: "Sudan" },
    engagement: { reposts: 310, likes: 820 },
    placeHints: ["Khartoum"],
    provenance: "public x query result",
    hoursAgo: 1
  },
  {
    id: "khartoum-bsky-1",
    sourceFamily: "bluesky",
    source: "Bluesky search",
    title: "Aid convoy delayed as crowds gather in Khartoum",
    rawText:
      "A Bluesky thread from local monitors says aid convoys were delayed while crowds gathered near Khartoum bridges. Mentions include protest activity and rumors of more mobilization.",
    language: "en",
    url: "https://bsky.example.com/khartoum-1",
    author: { name: "Sahel Monitor", profileLocation: "Northeast Africa" },
    engagement: { reposts: 78, likes: 192 },
    placeHints: ["Khartoum", "Sudan"],
    provenance: "public bluesky query result",
    hoursAgo: 4
  },
  {
    id: "yangon-news-1",
    sourceFamily: "news",
    source: "Irrawaddy Dispatch",
    title: "Yangon neighborhoods report anti-junta marches and fresh detentions",
    rawText:
      "Small anti-junta marches broke out across Yangon after overnight detentions. Residents described a visible military presence and road checks at major intersections.",
    language: "en",
    url: "https://example.com/yangon-1",
    author: { name: "Irrawaddy Dispatch", profileLocation: "Yangon" },
    engagement: { shares: 92, comments: 24 },
    placeHints: ["Yangon", "Myanmar"],
    provenance: "public news report",
    hoursAgo: 3
  },
  {
    id: "yangon-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "New convoy video from Yangon trends as crackdown rumors spread",
    rawText:
      "Video clips tagged from Yangon show convoy movement near government compounds. Posts discuss a possible purge of local commanders and a heavier military posture.",
    language: "en",
    url: "https://x.example.com/yangon-1",
    author: { name: "Burma Watch", profileLocation: "Myanmar" },
    engagement: { reposts: 510, likes: 1040 },
    placeHints: ["Yangon"],
    provenance: "public x query result",
    hoursAgo: 2
  },
  {
    id: "yangon-bsky-1",
    sourceFamily: "bluesky",
    source: "Bluesky search",
    title: "Thread tracks protest routes and internet slowdown in Yangon",
    rawText:
      "Observers on Bluesky mapped protest routes in Yangon and noted an internet slowdown after midnight. Replies mention riot police and army checkpoints.",
    language: "en",
    url: "https://bsky.example.com/yangon-1",
    author: { name: "Civic Mesh", profileLocation: "Southeast Asia" },
    engagement: { reposts: 61, likes: 145 },
    placeHints: ["Yangon", "Myanmar"],
    provenance: "public bluesky query result",
    hoursAgo: 6
  },
  {
    id: "quetta-news-1",
    sourceFamily: "news",
    source: "Frontier Journal",
    title: "Strike call in Quetta widens after arrests during protest march",
    rawText:
      "In Quetta, protest leaders called for a wider strike after arrests and clashes at a march. Security forces remained visible and a convoy was seen heading toward key roads.",
    language: "en",
    url: "https://example.com/quetta-1",
    author: { name: "Frontier Journal", profileLocation: "Pakistan" },
    engagement: { shares: 77, comments: 28 },
    placeHints: ["Quetta", "Pakistan"],
    provenance: "public news report",
    hoursAgo: 5
  },
  {
    id: "quetta-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "Balochistan thread points to convoy movement outside Quetta",
    rawText:
      "Multiple posts from Quetta and Balochistan mention troop movement and roadblocks after a protest wave. Some accounts claim dismissed officers were involved in internal disputes.",
    language: "en",
    url: "https://x.example.com/quetta-1",
    author: { name: "BorderlineINT", profileLocation: "Balochistan" },
    engagement: { reposts: 402, likes: 736 },
    placeHints: ["Quetta"],
    provenance: "public x query result",
    hoursAgo: 2
  },
  {
    id: "quetta-bsky-1",
    sourceFamily: "bluesky",
    source: "Bluesky search",
    title: "Analyst thread highlights roadblocks near Quetta and rumor spikes",
    rawText:
      "A cluster of Bluesky posts mentions roadblocks outside Quetta, rising protest traffic, and rumor-heavy claims about military mobilization. Cross-check requested.",
    language: "en",
    url: "https://bsky.example.com/quetta-1",
    author: { name: "Open South Asia", profileLocation: "Pakistan" },
    engagement: { reposts: 58, likes: 112 },
    placeHints: ["Quetta", "Pakistan"],
    provenance: "public bluesky query result",
    hoursAgo: 8
  },
  {
    id: "caracas-news-1",
    sourceFamily: "news",
    source: "Andes Daily",
    title: "Caracas rally met by National Guard deployment after opposition march expands",
    rawText:
      "An opposition march in Caracas expanded into nearby districts. The National Guard deployed barriers, and several detentions were reported after clashes near transit hubs.",
    language: "en",
    url: "https://example.com/caracas-1",
    author: { name: "Andes Daily", profileLocation: "Caracas" },
    engagement: { shares: 133, comments: 44 },
    placeHints: ["Caracas", "Venezuela"],
    provenance: "public news report",
    hoursAgo: 4
  },
  {
    id: "caracas-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "Dismissed officers rumor and transport disruptions trend in Caracas",
    rawText:
      "Posts from Caracas tie transport disruptions to National Guard deployments and a rumor that several officers were dismissed after criticizing the crackdown.",
    language: "en",
    url: "https://x.example.com/caracas-1",
    author: { name: "LatAm Lens", profileLocation: "Venezuela" },
    engagement: { reposts: 286, likes: 674 },
    placeHints: ["Caracas"],
    provenance: "public x query result",
    hoursAgo: 1
  },
  {
    id: "caracas-bsky-1",
    sourceFamily: "bluesky",
    source: "Bluesky search",
    title: "Local thread tracks march routes and anti-military slogans in Caracas",
    rawText:
      "A local Bluesky thread tracks protest routes in Caracas and notes stronger anti-military slogans after riot police and National Guard units moved into the area.",
    language: "en",
    url: "https://bsky.example.com/caracas-1",
    author: { name: "Observa Caracas", profileLocation: "Distrito Capital" },
    engagement: { reposts: 64, likes: 121 },
    placeHints: ["Caracas", "Venezuela"],
    provenance: "public bluesky query result",
    hoursAgo: 6
  },
  {
    id: "pap-news-1",
    sourceFamily: "news",
    source: "Caribbean Wire",
    title: "Port-au-Prince neighborhoods shut roads as clashes spread",
    rawText:
      "Residents in Port-au-Prince closed roads after overnight clashes. Security forces and local protection groups exchanged fire while schools and markets stayed shut.",
    language: "en",
    url: "https://example.com/pap-1",
    author: { name: "Caribbean Wire", profileLocation: "Haiti" },
    engagement: { shares: 111, comments: 32 },
    placeHints: ["Port-au-Prince", "Haiti"],
    provenance: "public news report",
    hoursAgo: 3
  },
  {
    id: "pap-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "Witness posts from Port-au-Prince describe roadblocks and security panic",
    rawText:
      "Witness posts from Port-au-Prince describe roadblocks, fires, and a rapidly spreading panic. Some posts mention police shortages but little direct military presence.",
    language: "en",
    url: "https://x.example.com/pap-1",
    author: { name: "Island Watch", profileLocation: "Port-au-Prince" },
    engagement: { reposts: 350, likes: 904 },
    placeHints: ["Port-au-Prince"],
    provenance: "public x query result",
    hoursAgo: 2
  },
  {
    id: "pap-bsky-1",
    sourceFamily: "bluesky",
    source: "Bluesky search",
    title: "Mutual-aid accounts warn of fresh clashes in Port-au-Prince",
    rawText:
      "Mutual-aid accounts on Bluesky warn of fresh clashes in Port-au-Prince and urge civilians to avoid transport hubs after security incidents and looting reports.",
    language: "en",
    url: "https://bsky.example.com/pap-1",
    author: { name: "Haiti Mutual Aid", profileLocation: "Ayiti" },
    engagement: { reposts: 47, likes: 89 },
    placeHints: ["Port-au-Prince", "Haiti"],
    provenance: "public bluesky query result",
    hoursAgo: 7
  },
  {
    id: "guayaquil-news-1",
    sourceFamily: "news",
    source: "Pacific Signal",
    title: "Emergency declaration renewed around Guayaquil after prison unrest",
    rawText:
      "Officials renewed emergency measures around Guayaquil after prison unrest and politically motivated violence disrupted transport corridors.",
    language: "en",
    url: "https://example.com/guayaquil-1",
    author: { name: "Pacific Signal", profileLocation: "Ecuador" },
    engagement: { shares: 65, comments: 21 },
    placeHints: ["Guayaquil", "Ecuador"],
    provenance: "public news report",
    hoursAgo: 10
  },
  {
    id: "guayaquil-x-1",
    sourceFamily: "x",
    source: "X search",
    title: "Road closures and security force movement reported in Guayaquil",
    rawText:
      "Posts from Guayaquil mention road closures, armed patrols, and a state of emergency after prison-linked violence flared again.",
    language: "en",
    url: "https://x.example.com/guayaquil-1",
    author: { name: "Pacific Watchfloor", profileLocation: "Guayaquil" },
    engagement: { reposts: 171, likes: 284 },
    placeHints: ["Guayaquil"],
    provenance: "public x query result",
    hoursAgo: 9
  },
  {
    id: "abuja-news-1",
    sourceFamily: "news",
    source: "Sahel Current",
    title: "Abuja march grows after new accusations of election-linked interference",
    rawText:
      "A march in Abuja grew into a broader protest as allegations of election-linked interference spread. Security forces stayed visible but calm while online rumor activity surged.",
    language: "en",
    url: "https://example.com/abuja-1",
    author: { name: "Sahel Current", profileLocation: "Nigeria" },
    engagement: { shares: 59, comments: 20 },
    placeHints: ["Abuja", "Nigeria"],
    provenance: "public news report",
    hoursAgo: 12
  },
  {
    id: "tripoli-news-1",
    sourceFamily: "news",
    source: "Mediterranean Brief",
    title: "Tripoli officials deny coup rumor after convoy movement draws attention",
    rawText:
      "In Tripoli, Libyan officials denied a coup rumor after convoy movement around ministry buildings. The article says the military posture remained unusual overnight.",
    language: "en",
    url: "https://example.com/tripoli-1",
    author: { name: "Mediterranean Brief", profileLocation: "Libya" },
    engagement: { shares: 96, comments: 27 },
    placeHints: ["Tripoli", "Libya"],
    provenance: "public news report",
    hoursAgo: 11
  }
];
