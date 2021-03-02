import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { SharedModule } from './shared/shared.module';
import { AppState } from './appStore/app.store';
import { NgxsModule } from '@ngxs/store';
import { NgxsRouterPluginModule } from '@ngxs/router-plugin';
import { NgxsReduxDevtoolsPluginModule } from '@ngxs/devtools-plugin';
import { NgxsLoggerPluginModule } from '@ngxs/logger-plugin';
import { environment } from '../environments/environment';
import { ColorSchemeService } from './shared/services/color-scheme.service';
import { CoreModule } from './@core/core.module';
import { DBGuard } from './guards/db.guard';
import { PageNotFoundComponent } from './page-not-found/page-not-found.component';
import { NgxsStoragePluginModule } from '@ngxs/storage-plugin';
@NgModule({
  declarations: [AppComponent, PageNotFoundComponent],
  imports: [
    BrowserModule,
    CoreModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    SharedModule,
    NgxsModule.forRoot([AppState]),
    NgxsRouterPluginModule.forRoot(),
    NgxsReduxDevtoolsPluginModule.forRoot({ name: 'App Store' }),
    NgxsStoragePluginModule.forRoot({
      key: ['app.dbUrl'],
    }),
    environment.production ? [] : NgxsLoggerPluginModule.forRoot(),
  ],
  providers: [ColorSchemeService, DBGuard],
  bootstrap: [AppComponent],
})
export class AppModule {}
