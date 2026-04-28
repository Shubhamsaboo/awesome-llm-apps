import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

// Get the app to build from environment variable or default to fitness-app
const app = process.env.BUILD_APP || "fitness-app";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "dist",
    emptyOutDir: false, // Don't clear dist so we can build multiple apps
    rollupOptions: {
      input: `${app}.html`,
      output: {
        entryFileNames: `${app}.js`,
        assetFileNames: `${app}.[ext]`,
      },
    },
  },
});
