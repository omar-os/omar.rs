import { getCollection, type CollectionEntry } from "astro:content";

export type DevPage = CollectionEntry<"devdocs">;

/** What a version's docs describe, written by scripts/devdocs.mjs. */
export interface DevMeta {
  ref: string;
  commit: string;
  synced: string;
}

const metas = import.meta.glob<DevMeta>("../content/devdocs/*/_meta.json", {
  eager: true,
  import: "default",
});

/** `v0.4.10` sorts after `v0.4.9`. */
function compareTags(a: string, b: string): number {
  const parts = (tag: string) =>
    tag.replace(/^v/, "").split(/[.-]/).map(Number);
  const [x, y] = [parts(a), parts(b)];
  for (let i = 0; i < Math.max(x.length, y.length); i++) {
    const d = (x[i] || 0) - (y[i] || 0);
    if (d) return d;
  }
  return 0;
}

export interface DevVersion {
  name: string;
  meta?: DevMeta;
  pages: { slug: string; page: DevPage }[];
}

/** `main` first, then releases newest first. */
export async function devVersions(): Promise<DevVersion[]> {
  const entries = await getCollection("devdocs");
  const byVersion = new Map<string, DevVersion>();
  for (const page of entries) {
    const [name, slug] = page.id.split("/");
    if (!byVersion.has(name)) {
      const meta = metas[`../content/devdocs/${name}/_meta.json`];
      byVersion.set(name, { name, meta, pages: [] });
    }
    byVersion.get(name)!.pages.push({ slug, page });
  }
  for (const version of byVersion.values()) {
    version.pages.sort((a, b) => a.page.data.order - b.page.data.order);
  }
  return [...byVersion.values()].sort((a, b) =>
    a.name === "main"
      ? -1
      : b.name === "main"
        ? 1
        : compareTags(b.name, a.name),
  );
}

export const devHref = (base: string, version: string, slug?: string) =>
  `${base}docs/dev/${version}/${slug ? `${slug}/` : ""}`;
