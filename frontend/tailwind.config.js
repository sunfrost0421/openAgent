/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        user: {
          bg: '#dbeafe',
          text: '#1e40af',
        },
        ai: {
          bg: '#f1f5f9',
          text: '#1e293b',
        },
        sidebar: {
          bg: '#f8fafc',
        },
      },
      maxWidth: {
        'chat-bubble': '70%',
      },
    },
  },
  plugins: [],
}
