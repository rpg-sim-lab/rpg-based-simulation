// @ts-check

// The site is a wiki for someone watching the simulation run. Its World Knowledge pages are a
// view of the repository's stored data (world rules, mechanism registry, content catalog),
// generated at build time by scripts/generate_wiki.py; docs/ itself is not rendered here
// (owner, #715 6789714730 and 6789779149).

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'RPG Simulation Wiki',
  url: process.env.DOCS_URL || 'http://localhost',
  baseUrl: process.env.DOCS_BASE_URL || '/',
  onBrokenLinks: 'throw',
  trailingSlash: false,
  markdown: {
    format: 'md',
    hooks: { onBrokenMarkdownLinks: 'throw' },
  },

  plugins: [],

  themes: [
    [
      require.resolve('@easyops-cn/docusaurus-search-local'),
      {
        hashed: false,
        docsRouteBasePath: ['wiki'],
        indexBlog: false,
      },
    ],
  ],

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'wiki',
          routeBasePath: 'wiki',
          sidebarPath: require.resolve('./sidebars.js'),
        },
        blog: false,
        theme: { customCss: [require.resolve('./src/css/custom.css')] },
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'RPG Simulation Wiki',
      items: [
        { type: 'docSidebar', sidebarId: 'worldKnowledge', label: 'World Knowledge', position: 'left' },
        { type: 'docSidebar', sidebarId: 'technical', label: 'Technical', position: 'left' },
        { type: 'docSidebar', sidebarId: 'controlGuide', label: 'Control Guide', position: 'left' },
      ],
    },
  },
};

module.exports = config;
