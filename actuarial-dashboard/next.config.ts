import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow ngrok cross-origin access in dev mode
  allowedDevOrigins: [
    "https://gone-elevator-brewery.ngrok-free.dev",
    "*.ngrok-free.dev",
    "*.ngrok-free.app",
    "*.ngrok.io",
    "*.vercel.app",
  ],
  experimental: {
    serverActions: {
      bodySizeLimit: "50mb",
    },
  },
};

export default nextConfig;
