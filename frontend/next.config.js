/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  // 禁用压缩以修复生产环境样式问题
  swcMinify: false,
  compiler: {
    removeConsole: false,
  },
};

module.exports = nextConfig;
