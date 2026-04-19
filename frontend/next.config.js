/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['leaflet', 'react-leaflet'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.tile.openstreetmap.org' },
    ],
  },
  webpack: (config) => {
    config.optimization.minimize = false;
    return config;
  },
}

module.exports = nextConfig
