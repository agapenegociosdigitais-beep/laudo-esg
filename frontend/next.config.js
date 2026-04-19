/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['leaflet', 'react-leaflet'],
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.tile.openstreetmap.org' },
    ],
  },
}

module.exports = nextConfig
