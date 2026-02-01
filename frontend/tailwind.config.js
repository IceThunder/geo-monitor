/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  purge: false,
  safelist: [
    // 背景色
    'bg-white', 'bg-gray-50', 'bg-gray-100', 'bg-gray-800', 'bg-gray-900',
    'bg-blue-50', 'bg-blue-100', 'bg-blue-600', 'bg-blue-900',
    'bg-green-50', 'bg-green-100', 'bg-green-600', 'bg-green-900',
    'bg-purple-50', 'bg-purple-100', 'bg-purple-600', 'bg-purple-900',
    'bg-orange-50', 'bg-orange-100', 'bg-orange-600', 'bg-orange-900',
    'bg-red-50', 'bg-red-100', 'bg-red-600', 'bg-red-900',
    'bg-yellow-50', 'bg-yellow-100', 'bg-yellow-600', 'bg-yellow-900',
    // 文字颜色
    'text-white', 'text-gray-400', 'text-gray-500', 'text-gray-600', 'text-gray-700', 'text-gray-800', 'text-gray-900',
    'text-blue-400', 'text-blue-600', 'text-blue-800', 'text-blue-900',
    'text-green-400', 'text-green-600', 'text-green-800', 'text-green-900',
    'text-purple-400', 'text-purple-600', 'text-purple-800', 'text-purple-900',
    'text-orange-400', 'text-orange-600', 'text-orange-800', 'text-orange-900',
    'text-red-400', 'text-red-600', 'text-red-800', 'text-red-900',
    'text-yellow-400', 'text-yellow-600', 'text-yellow-800', 'text-yellow-900',
    // 布局
    'grid', 'grid-cols-1', 'grid-cols-2', 'grid-cols-3', 'grid-cols-4',
    'md:grid-cols-2', 'md:grid-cols-3', 'md:grid-cols-4',
    'lg:grid-cols-2', 'lg:grid-cols-3', 'lg:grid-cols-4',
    'flex', 'flex-1', 'flex-col', 'flex-row', 'inline-flex',
    'items-center', 'items-start', 'items-end', 'justify-center', 'justify-between', 'justify-start', 'justify-end',
    // 间距
    'p-0', 'p-1', 'p-2', 'p-3', 'p-4', 'p-6', 'p-8',
    'px-2', 'px-3', 'px-4', 'px-6', 'px-8',
    'py-2', 'py-3', 'py-4', 'py-6', 'py-8',
    'm-0', 'm-1', 'm-2', 'm-3', 'm-4', 'm-6', 'm-8',
    'mx-2', 'mx-3', 'mx-4', 'mx-6', 'mx-8', 'mx-auto',
    'my-2', 'my-3', 'my-4', 'my-6', 'my-8',
    'space-x-1', 'space-x-2', 'space-x-3', 'space-x-4', 'space-x-6',
    'space-y-1', 'space-y-2', 'space-y-3', 'space-y-4', 'space-y-6',
    // 边框和圆角
    'border', 'border-0', 'border-2', 'border-gray-200', 'border-gray-300', 'border-blue-200', 'border-green-200',
    'rounded', 'rounded-lg', 'rounded-xl', 'rounded-full', 'rounded-md', 'rounded-sm',
    // 阴影
    'shadow', 'shadow-sm', 'shadow-md', 'shadow-lg',
    // 字体
    'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl', 'text-2xl', 'text-3xl',
    'font-medium', 'font-semibold', 'font-bold',
    // 宽高
    'w-full', 'w-auto', 'w-8', 'w-10', 'w-12', 'w-16', 'w-20', 'w-32',
    'h-full', 'h-auto', 'h-8', 'h-10', 'h-12', 'h-16', 'h-20', 'h-32', 'h-80',
    // 其他常用类
    'relative', 'absolute', 'fixed', 'sticky', 'block', 'hidden', 'inline-block',
    'transition-colors', 'hover:bg-accent', 'hover:text-accent-foreground',
    'focus-visible:outline-none', 'focus-visible:ring-2', 'focus-visible:ring-ring',
    'disabled:pointer-events-none', 'disabled:opacity-50',
    'min-h-screen', 'max-w-lg', 'overflow-hidden', 'cursor-pointer'
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
