import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");
const files = [
  ".next/types/app/api/samples/[name]/route.ts",
  ".next/types/app/layout.ts",
  ".next/types/app/page.ts",
  ".next/types/cache-life.d.ts",
  ".next/types/link.d.ts"
];

for (const relativeFile of files) {
  const absoluteFile = path.join(webRoot, relativeFile);
  await mkdir(path.dirname(absoluteFile), { recursive: true });
  await writeFile(
    absoluteFile,
    "export {};\n"
  );
}
