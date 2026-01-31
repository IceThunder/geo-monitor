/**
 * Root Layout - Google Style
 */
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { GoogleLayout } from '@/components/layout/google-layout';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'GEO Monitor - AI 模型品牌监控平台',
  description: '实时监控品牌在 ChatGPT、Claude、Gemini 等 AI 模型中的表现',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <GoogleLayout>
          {children}
        </GoogleLayout>
      </body>
    </html>
  );
}
