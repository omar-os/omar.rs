// @ts-check
import { defineConfig } from "astro/config";

// https://astro.build/config
export default defineConfig({
  output: "static",
  site: "https://omarmy.ai",
  build: {
    assets: "assets",
  },
});
