import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const distDir = path.resolve(rootDir, "dist");

async function main() {
  await rm(distDir, { recursive: true, force: true });
  await mkdir(distDir, { recursive: true });
  await cp(path.join(rootDir, "index.html"), path.join(distDir, "index.html"));
  await cp(path.join(rootDir, "src"), path.join(distDir, "src"), { recursive: true });
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
