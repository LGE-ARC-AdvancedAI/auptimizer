/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
import { State, Selector, Action, StateContext } from '@ngxs/store';
import { Injectable } from '@angular/core';
import { AppStateModel, Theme } from './app-state.model';
import {
  SetTheme,
  ChangeTheme,
  GetDatabaseLink,
  AddNotification,
  RemoveNotification,
  RemoveAllNotifications,
  GetNotifications,
} from './app.actions';
import { ColorSchemeService } from '../shared/services/color-scheme.service';
import { AppService } from '../app.service';
import { catchError, map } from 'rxjs/operators';
import { HttpErrorResponse } from '@angular/common/http';
import { throwError } from 'rxjs';
import { SnackbarService, UtilsService } from '../shared/services';
import { AppNotification } from './app-state.model';
import { THEME_OPTION } from '../models/enum/theme-option.enum';

@State<AppStateModel>({
  name: 'app',
  defaults: {
    theme: null,
    themes: [
      {
        name: THEME_OPTION.DARK,
        icon: 'brightness_3',
      },
      {
        name: THEME_OPTION.LIGHT,
        icon: 'wb_sunny',
      },
    ],
    dbUrl: null,
    notifications: [],
    notificationExpiration: 86400, // 1 day in seconds
  },
})
@Injectable()
export class AppState {
  @Selector()
  static theme(state: AppStateModel): Theme {
    return state.theme;
  }
  @Selector()
  static dbUrl(state: AppStateModel): string {
    return state.dbUrl;
  }
  @Selector()
  static isDbUrl(state: AppStateModel): boolean {
    return !!state.dbUrl;
  }
  @Selector()
  static themes(state: AppStateModel): Theme[] {
    return state.themes;
  }
  @Selector()
  static notifications(state: AppStateModel): AppNotification[] {
    return state.notifications;
  }

  constructor(
    public colorSchemeService: ColorSchemeService,
    private appService: AppService,
    private snackbarService: SnackbarService,
    readonly utilsService: UtilsService
  ) {}

  @Action(SetTheme)
  setTheme(ctx: StateContext<AppStateModel>): void {
    const state = ctx.getState();
    const localTheme = this.colorSchemeService.currentActive();
    const currentTheme = state.themes.filter((theme) => theme.name === localTheme)[0];
    ctx.setState({
      ...state,
      theme: currentTheme,
    });
  }

  @Action(ChangeTheme)
  changeTheme(ctx: StateContext<AppStateModel>, { payload }: ChangeTheme): void {
    const state = ctx.getState();
    const currentTheme = payload;
    ctx.setState({
      ...state,
      theme: currentTheme,
    });
    return this.colorSchemeService.update(payload.name);
  }

  @Action(AddNotification)
  addNotifications(ctx: StateContext<AppStateModel>, { payload }: AddNotification): void {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    const notifications = state.notifications.slice();
    const index = notifications.indexOf(payload);
    if (index === -1) {
      notifications.push(payload);
    }
    ctx.patchState({ notifications });
    localStorage.setItem('notifications', JSON.stringify(notifications));
    return;
  }

  @Action(RemoveNotification)
  removeNotifications(ctx: StateContext<AppStateModel>, { payload }: RemoveNotification): void {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    const notifications = state.notifications.slice();
    const index = notifications.indexOf(payload);
    notifications.splice(index, 1);
    ctx.patchState({ notifications });
    localStorage.setItem('notifications', JSON.stringify(notifications));
    return;
  }

  @Action(RemoveAllNotifications)
  removeAllNotifications(ctx: StateContext<AppStateModel>): void {
    const notifications = [];
    ctx.patchState({ notifications });
    localStorage.setItem('notifications', JSON.stringify(notifications));
    return;
  }

  @Action(GetNotifications)
  getNotifications(ctx: StateContext<AppStateModel>): void {
    const allNotifications = (JSON.parse(localStorage.getItem('notifications')) as AppNotification[]) || [];
    const expiry = ctx.getState().notificationExpiration;
    const now = new Date().getTime();
    const notifications = allNotifications.filter((notification: AppNotification) => {
      const difference = (now - notification.receivedAt) / 1000;
      if (expiry > difference) {
        return notification;
      }
    });
    ctx.patchState({
      notifications,
    });
    localStorage.setItem('notifications', JSON.stringify(notifications));
    return;
  }

  @Action(GetDatabaseLink)
  getDatabaseLink(ctx: StateContext<AppStateModel>): void {
    return this.appService.getDatabaseLink().pipe(
      catchError((err: HttpErrorResponse) => {
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res && res['db_path']) {
          ctx.patchState({
            dbUrl: res['db_path'] as string,
          });
          return;
        }
      })
    );
  }
}
