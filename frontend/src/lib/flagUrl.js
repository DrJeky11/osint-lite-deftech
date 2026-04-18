// Resolve flag URL from circle-flags SVGs served from public/flags/ (airgap-safe)
const FALLBACK = '/flags/xx.svg';

export function getFlagUrl(countryCode) {
  if (!countryCode) return FALLBACK;
  return `/flags/${countryCode.toLowerCase()}.svg`;
}
