import { getFlagUrl } from './flagUrl.js';

/**
 * Load a circular flag image into the MapLibre map.
 * Image ID: `flag-{countryCode}` (lowercase).
 */
export async function loadFlagImage(map, countryCode) {
  if (!countryCode) return;
  const code = countryCode.toLowerCase();
  const flagId = `flag-${code}`;
  if (map.hasImage(flagId)) return;

  const size = 32;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext('2d');

  const imgUrl = getFlagUrl(code);

  try {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    const loaded = new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
    });
    img.src = imgUrl;
    await loaded;

    ctx.save();

    // Circular clip
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.clip();

    // White background
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Draw flag centered & covering
    const scale = Math.max(size / img.width, size / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    const x = (size / 2) - (w / 2);
    const y = (size / 2) - (h / 2);
    ctx.drawImage(img, x, y, w, h);

    ctx.restore();

    // Border
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, (size / 2) - 1, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 2;
    ctx.stroke();

    const imageData = ctx.getImageData(0, 0, size, size);
    if (!map.hasImage(flagId)) {
      map.addImage(flagId, imageData);
    }
  } catch (err) {
    console.error(`Failed to load flag for ${countryCode}`);

    // Fallback: draw country code initials in a circle
    ctx.fillStyle = '#333';
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 12px "Open Sans", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(countryCode.toUpperCase().substring(0, 2), size / 2, size / 2);

    ctx.beginPath();
    ctx.arc(size / 2, size / 2, (size / 2) - 1, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 2;
    ctx.stroke();

    const imageData = ctx.getImageData(0, 0, size, size);
    if (!map.hasImage(flagId)) {
      map.addImage(flagId, imageData);
    }
  }
}
