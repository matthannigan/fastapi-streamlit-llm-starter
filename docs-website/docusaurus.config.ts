import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const config: Config = {
  title: 'FastAPI + Streamlit LLM Starter Template',
  tagline: 'Starter template for web-based LLM app with FastAPI backend and Streamlit frontend',
  favicon: 'favicon/favicon.ico',

  // Set the production url of your site here
  url: 'https://matthannigan.github.io', // Replace with your GitHub username
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/fastapi-streamlit-llm-starter/', // Replace with your repo name

  // GitHub pages deployment config.
  organizationName: 'matthannigan', // Replace with your GitHub org/user name
  projectName: 'fastapi-streamlit-llm-starter', // Replace with your repo name
  trailingSlash: undefined,
  deploymentBranch: 'gh-pages',

  markdown: {
    format: 'detect', // Use CommonMark for .md and MDX for .mdx
    mermaid: true,
  },

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  onBrokenLinks: 'ignore', //'throw',
  onBrokenMarkdownLinks: 'ignore', //'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          path: '../docs',
          sidebarPath: './sidebars.ts',
          // This sets the /docs path as the default route
          routeBasePath: '/',
          // Update this to your repo
          // editUrl:
          //   'https://github.com/matthannigan/fastapi-streamlit-llm-starter/tree/main/docs-website/',
          // --- ADDED: Exclude patterns ---
          exclude: [
            // Exclude files/directories starting with an underscore (common for drafts/partials)
            '**/_*.*',
            '**/_*/**',
            // Exclude any directory named 'templates' and its contents
            '**/templates/**/*',
            // Exclude files ending with .template.md or .template.mdx
            '**/*-template.{md,mdx}',
            // Add any other specific files or patterns needed
            // '**/my-specific-template.md',
          ],
          // --- End of Added Section ---
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  // plugins: [
  //   [
  //     require.resolve('docusaurus-lunr-search'),
  //     {
  //       languages: ['en'],
  //       indexBaseUrl: true,
  //     },
  //   ],
  // ],
  
  themes: ['@docusaurus/theme-mermaid'],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'FastAPI + Streamlit LLM Starter Template',
      logo: {
        alt: 'Project Logo',
        src: 'img/logo.svg',
      },
      items: [
        /*{
          type: 'docSidebar',
          sidebarId: 'readme',
          position: 'left',
          label: 'READMEs',
        },*/
        {
          type: 'docSidebar',
          sidebarId: 'docs',
          position: 'left',
          label: 'Documentation',
        },
        {
          type: 'docSidebar',
          sidebarId: 'deep_dives',
          position: 'left',
          label: 'Technical Deep Dives',
        },
        {
          type: 'docSidebar',
          sidebarId: 'code_ref',
          position: 'left',
          label: 'Code Reference',
        },
        {
          href: 'https://github.com/matthannigan/fastapi-streamlit-llm-starter/',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    /*footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Tutorial',
              to: '/docs/intro',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'Stack Overflow',
              href: 'https://stackoverflow.com/questions/tagged/docusaurus',
            },
            {
              label: 'Discord',
              href: 'https://discordapp.com/invite/docusaurus',
            },
            {
              label: 'X',
              href: 'https://x.com/docusaurus',
            },
          ],
        },
        {
          title: 'More',
          items: [
            {
              label: 'Blog',
              to: '/blog',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/facebook/docusaurus',
            },
          ],
        },
      ],
      //copyright: `Copyright © ${new Date().getFullYear()} FastAPI + Streamlit LLM Starter Template. Built with Docusaurus.`,
      copyright: `Built with <a href="https://docusaurus.io/" target="_blank">Docusaurus</a>.`,
    },*/
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'diff', 'json', 'python'],
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },    
  } satisfies Preset.ThemeConfig,
};

export default config;
