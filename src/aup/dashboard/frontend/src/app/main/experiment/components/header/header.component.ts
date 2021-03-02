/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { environment } from '../../../../../environments/environment';
import { MatSelectChange } from '@angular/material/select';
import { Store, Select } from '@ngxs/store';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription } from 'rxjs';
import { SetRefreshInterval, RefreshInterval, ToggleSideNav } from '../../store/experiment.actions';
import { ColorSchemeService } from '../../../../shared/services/color-scheme.service';
import { AppState } from '../../../../appStore/app.store';
import { AppNotification, Theme } from '../../../../appStore/app-state.model';
import { ChangeTheme } from '../../../../appStore/app.actions';
import { HelperService } from '../../../../shared/services';
import { THEME_OPTION } from '../../../../models/enum/theme-option.enum';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-header',
  templateUrl: './header.component.html',
  styleUrls: ['./header.component.scss'],
})
export class HeaderComponent implements OnInit, OnDestroy {
  @Select(AppState.themes) themes$: Observable<Theme[]>;
  @Select(AppState.theme) theme$: Observable<Theme>;
  @Select(AppState.notifications) notifications$: Observable<AppNotification[]>;
  @Select(ExperimentState.refreshInterval) refreshInterval$: Observable<number>;
  @Select(ExperimentState.refreshIntervalOptions) refreshIntervalOptions$: Observable<number[]>;
  @Select(ExperimentState.sidenavOpen) sidenavOpen$: Observable<boolean>;

  version: string;
  subscriptions: Subscription;
  notifications: AppNotification[];
  THEME_OPTION = THEME_OPTION;

  public themes;
  currentTheme = {
    name: null,
    icon: null,
  };

  constructor(
    readonly store: Store,
    public colorSchemeService: ColorSchemeService,
    public helperService: HelperService,
    private cdRef: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.version = environment.version;
    this.subscriptions.add(
      this.themes$.subscribe((themes: Theme[]) => {
        this.themes = themes;
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        this.currentTheme = theme;
      })
    );
    this.subscriptions.add(
      this.notifications$.subscribe((notifications: AppNotification[]) => {
        if (notifications) {
          this.notifications = notifications;
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        this.currentTheme = theme;
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  changeRefreshInverval(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    this.store.dispatch(new SetRefreshInterval(event.value));
  }

  onRefresh(): void {
    this.store.dispatch(new RefreshInterval(true));
  }

  setTheme(): void {
    if (this.themes && this.themes.length) {
      if (this.currentTheme === this.themes[0]) {
        this.currentTheme = this.themes[1];
      } else {
        this.currentTheme = this.themes[0];
      }
      this.store.dispatch(new ChangeTheme(this.currentTheme));
    }
  }

  onToggleSideNav(): void {
    this.store.dispatch(new ToggleSideNav());
  }
}
