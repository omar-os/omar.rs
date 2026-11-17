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
      if (
        (node.type === "html" || node.type === "mdxJsxFlowElement") &&
        typeof node.value === "string"
      ) {
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

// Developer docs link each other as `overview.md`, which reads on GitHub and
// in an editor; on the site that page is `../overview/` (every developer docs
// page is /docs/dev/<version>/<page>/).
function remarkDevdocsLinks() {
  return (tree, file) => {
    if (!file.path?.includes("/src/content/devdocs/")) return;
    visit(tree, "link", (node) => {
      const match = /^([a-z0-9-]+)\.md(#.*)?$/.exec(node.url);
      if (match) node.url = `../${match[1]}/${match[2] ?? ""}`;
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
      theme: "github-dark",
    },
    remarkPlugins: [remarkBaseUrl, remarkDevdocsLinks],
  },
});
