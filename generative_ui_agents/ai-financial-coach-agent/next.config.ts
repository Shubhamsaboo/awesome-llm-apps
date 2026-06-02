import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  serverExternalPackages: ["@copilotkit/runtime"],
  typescript: {
    // HttpAgent type mismatch with CopilotRuntime — pending upstream fix in @copilotkit/runtime
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
