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
        text: 'Introduction',
        link: '/'
      },
      {
        text: 'Client',
        items: [
          { text: 'API', link: '/api' }, 
          { text: 'Pody CLI', link: '/pody-cli' }, 
        ]
      }, 
      {
        text: 'Deployment',
        items: [
          { text: 'Basic', link: '/deploy/' },
          { text: 'Remote User Profile', link: '/deploy/remote_user_profile' },
          { text: 'Start on Boot', link: '/deploy/start_on_boot' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/menxli/pody' }
    ]
  }
})
