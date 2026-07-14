// @ts-check
import { defineConfig } from "astro/config";
import { visit } from "unist-util-visit";

const base = process.env.ASTRO_BASE ?? "/";

function remarkBaseUrl() {
  return (tree) => {
    if (base === "/") return;
    const prefix = base.replace(/\/$/, "");
    const rewriteAttr = (input) =>
      input.replace(
        /\b(src|href)=("|')(\/(?!\/)[^"']*)\2/g,
        (match, attr, quote, url) =>
          url.startsWith(prefix + "/") || url === prefix
            ? match
            : `${attr}=${quote}${prefix}${url}${quote}`,
      );
    visit(tree, (node) => {
      if ((node.type === "html" || node.type === "mdxJsxFlowElement") && typeof node.value === "string") {
        node.value = rewriteAttr(node.value);
      }
      if (node.type === "image" && typeof node.url === "string") {
        if (
          node.url.startsWith("/") &&
          !node.url.startsWith("//") &&
          !node.url.startsWith(prefix + "/")
        ) {
          node.url = prefix + node.url;
        }
      }
    });
  };
}

// https://astro.build/config
export default defineConfig({
  base,
  output: "static",
  site: "https://omar.rs",
  build: {
    assets: "assets",
  },
  markdown: {
    shikiConfig: {
      theme: "github-light",
    },
    remarkPlugins: [remarkBaseUrl],
  },
});
