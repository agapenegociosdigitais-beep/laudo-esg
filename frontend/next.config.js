/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['leaflet', 'react-leaflet'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.tile.openstreetmap.org' },
    ],
  },
  staticPageGenerationTimeout: 1000,
  experimental: {
    isrMemoryCacheSize: 0,
  },
}

module.exports = nextConfig
