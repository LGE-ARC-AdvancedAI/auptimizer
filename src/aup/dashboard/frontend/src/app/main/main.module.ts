import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { MainRoutingModule } from './main-routing.module';
import * as fromContainers from './containers';
import { SharedModule } from '../shared/shared.module';

@NgModule({
  declarations: [...fromContainers.containers],
  imports: [CommonModule, MainRoutingModule, SharedModule],
})
export class MainModule {}
