/* eslint-disable prefer-arrow/prefer-arrow-functions */
import { NgModule, APP_INITIALIZER } from '@angular/core';

import { HttpClientModule } from '@angular/common/http';
import { AppLoadService } from './app-load.service';
import { ColorSchemeService } from '../shared/services/color-scheme.service';

export function initializeApplication(appLoadService: AppLoadService) {
  // eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
  return () => appLoadService.initializeApplication();
}
// we can add more initializers in the future. As long as they dont depend
// each other we can add new provider and make them run in parallel
@NgModule({
  imports: [HttpClientModule],
  providers: [
    AppLoadService,
    ColorSchemeService,
    { provide: APP_INITIALIZER, useFactory: initializeApplication, deps: [AppLoadService], multi: true },
  ],
})
export class CoreModule {}
