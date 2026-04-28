import type { NextConfig } from "next";
import dotenv from "dotenv";

dotenv.config({
  path: "../../.env",
});

const nextConfig: NextConfig = {
  output: "standalone",
  serverExternalPackages: ["@copilotkit/runtime"],
  /** Bundle prebuilt monorepo shell for full-kit workspace download (see prebuild / pack-download-kit). */
  outputFileTracingIncludes: {
    "/api/workspace/download": [".download-kit/base.tar.gz"],
  },
};

export default nextConfig;
