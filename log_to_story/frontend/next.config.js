/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
  },
  // Allow images from any domain (if needed)
  images: {
    domains: [],
  },
  // Memory optimization settings
  swcMinify: true,
  productionBrowserSourceMaps: false,
  optimizeFonts: false,
  experimental: {
    workerThreads: false,
    cpus: 1,
  },
}

module.exports = nextConfig
