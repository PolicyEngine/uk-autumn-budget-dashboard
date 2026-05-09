import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // recharts and d3 ship CJS interop and rely on browser globals; transpiling
  // them through Next's pipeline avoids ESM/CJS mismatch errors during build.
  transpilePackages: ['recharts', 'd3'],
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
