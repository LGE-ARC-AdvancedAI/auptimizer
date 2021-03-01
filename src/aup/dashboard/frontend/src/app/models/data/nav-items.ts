import { NavItem } from '../nav-items.model';

export const NAV_ITEMS: NavItem[] = [
  {
    displayName: 'Overview',
    route: 'overview',
    iconName: 'table_chart',
    tooltip: 'Overview',
  },
  {
    displayName: 'Job Status',
    route: 'job-status',
    iconName: 'science',
    tooltip: 'Job Status',
  },
  {
    displayName: 'Hyperparameter Interaction Graph',
    route: 'hig',
    iconName: 'bar_chart',
    tooltip: 'Hyperparameter Interaction Graph',
  },
  {
    displayName: 'Intermediate Results',
    route: 'interm',
    iconName: 'graphic_eq',
    tooltip: 'Intermediate Results',
  },
  {
    displayName: 'Multi-Experiment Comparison',
    route: 'multi',
    iconName: 'stacked_line_chart',
    tooltip: 'Multi-Experiment Comparison',
  },
];
