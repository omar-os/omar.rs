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

export const collections = { blog, "zh-blog": zhBlog };
