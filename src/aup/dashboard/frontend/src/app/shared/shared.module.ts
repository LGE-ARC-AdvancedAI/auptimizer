/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MaterialModule } from '../material/material.module';
import { FlexLayoutModule } from '@angular/flex-layout';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { NgxPaginationModule } from 'ngx-pagination';

import * as fromPipes from './pipes';
import * as fromServices from './services';

import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { PlotlyModule } from 'angular-plotly.js';
import { dialogs } from './dialogs';

PlotlyModule.plotlyjs = PlotlyJS;

@NgModule({
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MaterialModule, FlexLayoutModule, HttpClientModule],
  exports: [
    FormsModule,
    ReactiveFormsModule,
    MaterialModule,
    FlexLayoutModule,
    HttpClientModule,
    PlotlyModule,
    NgxPaginationModule,
    fromPipes.pipes,
  ],
  providers: [fromServices.services],
  declarations: [...dialogs, ...fromPipes.pipes],
})
export class SharedModule {}
