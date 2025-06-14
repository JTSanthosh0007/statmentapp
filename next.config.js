/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: '.next',
  experimental: {
    outputFileTracingExcludes: {
      '*': [
        './node_modules/@swc/core-win32-x64-msvc',
        './node_modules/esbuild',
        './node_modules/uglify-js',
      ],
    },
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback.fs = false;
    }
    return config;
  },
};

module.exports = nextConfig; 