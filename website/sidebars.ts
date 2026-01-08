import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docsSidebar: [
    {
      type: 'category',
      label: 'Open Telco',
      collapsed: false,
      items: [
        'welcome',
        'contributing',
      ],
    },
  ],
};

export default sidebars;
