import type { NextConfig } from "next";
import path from "node:path";

const nextConfig: NextConfig = {
  // Pin the workspace root (a stray lockfile in the home dir otherwise
  // confuses Next's root inference).
  turbopack: { root: path.resolve(__dirname) },
  experimental: {
    // Disable Turbopack's persistent filesystem cache: on this OneDrive-backed
    // path its background compaction blows the Node heap (OOM). Dev is a little
    // slower to recompile but stays stable.
    turbopackFileSystemCacheForDev: false,
  },
};

export default nextConfig;
