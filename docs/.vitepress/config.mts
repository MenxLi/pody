import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Pody-doc",
  base: "/pody/",     // set this for github pages
  description: "Documentation for pody manager.",
  lastUpdated: true,
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Introduction', link: '/' }, 
      { text: 'API', link: '/api' }, 
    ],

    sidebar: [
      {
        text: 'Pody Documentation',
        items: [
          { text: 'Introduction', link: '/' },
          { text: 'API', link: '/api' }, 
          { text: 'Pody CLI', link: '/pody-cli' }, 
          { text: 'Deployment', link: '/deploy' }, 
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/menxli/pody' }
    ]
  }
})
