import { defineConfig } from 'astro/config';

// GitHub Pages: el repo se llama data-analyst-ecosystem
// La URL será: https://leandrobenjaminl.github.io/data-analyst-ecosystem/
export default defineConfig({
  site: 'https://leandrobenjaminl.github.io',
  base: '/datlas',
  output: 'static',
  build: {
    assets: 'assets',
  },
});
