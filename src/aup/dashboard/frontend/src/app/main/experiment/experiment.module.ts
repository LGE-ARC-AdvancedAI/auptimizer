import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ExperimentRoutingModule } from './experiment-routing.module';
import { SharedModule } from '../../shared/shared.module';

import { NgxsModule } from '@ngxs/store';
import { ExperimentState } from './store/experiment.store';
import { ExperimentService } from './services/experiment.service';

import * as fromContainers from './containers';
import * as fromComponents from './components';
import { MatTableExporterModule } from 'mat-table-exporter';

@NgModule({
  declarations: [...fromContainers.containers, ...fromComponents.components],
  imports: [
    CommonModule,
    ExperimentRoutingModule,
    SharedModule,
    NgxsModule.forFeature([ExperimentState]),
    MatTableExporterModule,
  ],
  providers: [ExperimentService],
})
export class ExperimentModule {}
