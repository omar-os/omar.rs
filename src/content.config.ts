import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";

const authorSchema = z.union([
  z.string(),
  z.array(z.object({ name: z.string(), url: z.string().optional() })),
]);

const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    date: z.string(),
    author: authorSchema.optional(),
  }),
});

const zhBlog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/zh-blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    date: z.string(),
    author: authorSchema.optional(),
  }),
});

// Developer docs: src/content/devdocs/<version>/<page>.md, where <version> is
// `main` or a release tag. Kept in step with the OMAR code by
// scripts/devdocs.mjs (see .github/workflows/devdocs-nightly.yml).
const devdocs = defineCollection({
  loader: glob({
    pattern: "*/*.md",
    base: "./src/content/devdocs",
    // Keep `v0.4.4/overview` as is; the default id would slugify the dots.
    generateId: ({ entry }) => entry.replace(/\.md$/, ""),
  }),
  schema: z.object({
    title: z.string(),
    order: z.number(),
  }),
});

export const collections = { blog, "zh-blog": zhBlog, devdocs };
