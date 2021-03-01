import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import * as fromContainers from './containers';
import { DBGuard } from '../../guards/db.guard';

const routes: Routes = [
  {
    path: '',
    canActivate: [DBGuard],
    component: fromContainers.MainComponent,
    children: [
      { path: '', redirectTo: 'list', pathMatch: 'full' },
      {
        path: 'list',
        component: fromContainers.ListComponent,
      },
      {
        path: 'notification',
        component: fromContainers.NotificationComponent,
      },
      { path: 'create', component: fromContainers.CreateExperimentComponent },
      { path: 'create/:id', component: fromContainers.CreateExperimentComponent },
      {
        path: 'experiment/:id',
        component: fromContainers.ExperimentComponent,
        children: [
          { path: '', redirectTo: 'overview', pathMatch: 'full' },
          { path: 'overview', component: fromContainers.OverviewComponent },
          { path: 'job-status', component: fromContainers.JobStatusComponent },
          { path: 'hig', component: fromContainers.PcgComponent },
          { path: 'multi', component: fromContainers.MultiExpCompComponent },
          { path: 'interm', component: fromContainers.IntermResultsComponent },
        ],
      },
    ],
  },
  { path: 'initialize', component: fromContainers.InitializeComponent },
];
@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class ExperimentRoutingModule {}
