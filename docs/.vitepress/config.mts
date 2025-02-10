import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Pody-docs",
  description: "Documentation for pody manager.",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Introduction', link: '/intro' }
    ],

    sidebar: [
      {
        text: 'Pody Documentations',
        items: [
          { text: 'Introduction', link: '/intro' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/menxli/pody' }
    ]
  }
})
