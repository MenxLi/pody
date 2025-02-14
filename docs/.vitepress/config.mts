import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Pody-doc",
  base: "/docs/",
  description: "Documentation for pody manager.",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Introduction', link: '/intro' }, 
      { text: 'API', link: '/api' }, 
    ],

    sidebar: [
      {
        text: 'Pody Documentations',
        items: [
          { text: 'Introduction', link: '/intro' },
          { text: 'API', link: '/api' }, 
          { text: 'Pody CLI', link: '/pody-cli' }, 
          { text: 'Deploy', link: '/deploy' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/menxli/pody' }
    ]
  }
})
