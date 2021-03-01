import { MainComponent } from './main/main.component';
import { ExperimentComponent } from './experiment/experiment.component';
import { ListComponent } from './list/list.component';
import { OverviewComponent } from './overview/overview.component';
import { JobStatusComponent } from './job-status/job-status.component';
import { PcgComponent } from './pcg/pcg.component';
import { MultiExpCompComponent } from './multi-exp-comp/multi-exp-comp.component';
import { InitializeComponent } from './initialize/initialize.component';
import { CreateExperimentComponent } from './create-experiment/create-experiment.component';
import { IntermResultsComponent } from './interm-results/interm-results.component';
import { NotificationComponent } from './notification/notification.component';

export const containers = [
  MainComponent,
  ExperimentComponent,
  ListComponent,
  OverviewComponent,
  JobStatusComponent,
  PcgComponent,
  MultiExpCompComponent,
  InitializeComponent,
  CreateExperimentComponent,
  IntermResultsComponent,
  NotificationComponent,
];

export * from './main/main.component';
export * from './experiment/experiment.component';
export * from './list/list.component';
export * from './overview/overview.component';
export * from './job-status/job-status.component';
export * from './pcg/pcg.component';
export * from './multi-exp-comp/multi-exp-comp.component';
export * from './initialize/initialize.component';
export * from './create-experiment/create-experiment.component';
export * from './interm-results/interm-results.component';
export * from './notification/notification.component';
