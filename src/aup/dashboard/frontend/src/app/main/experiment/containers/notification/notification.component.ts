/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/unbound-method */
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatSelectChange } from '@angular/material/select';
import { Sort } from '@angular/material/sort';
import { Select, Store } from '@ngxs/store';
import { Observable, Subscription } from 'rxjs';
import { AppNotification } from '../../../../appStore/app-state.model';
import { RemoveAllNotifications, RemoveNotification } from '../../../../appStore/app.actions';
import { AppState } from '../../../../appStore/app.store';
import { NOTIFICATION_TYPE } from '../../../../models/enum/notification-type.enum';
import { HelperService, UtilsService } from '../../../../shared/services';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-notification',
  templateUrl: './notification.component.html',
  styleUrls: ['./notification.component.scss'],
})
export class NotificationComponent implements OnInit, OnDestroy {
  @Select(AppState.notifications) notifications$: Observable<AppNotification[]>;

  subscriptions: Subscription;
  readonly COLUMNS = {
    TYPE: 'Type',
    MESSAGE: 'Message',
    RECEIVED: 'Received at',
  };
  pageSize = 5;
  page = 1;

  NOTIFICATION_TYPE = NOTIFICATION_TYPE;
  notifications: AppNotification[];

  sortOptions = [this.COLUMNS.TYPE, this.COLUMNS.MESSAGE, this.COLUMNS.RECEIVED];
  sortOption = new FormControl(this.COLUMNS.RECEIVED);
  sortDirectionType: 'asc' | 'desc' = 'desc';
  sortDirections: ('asc' | 'desc')[] = ['asc', 'desc'];

  constructor(
    readonly store: Store,
    private cdRef: ChangeDetectorRef,
    public helperService: HelperService,
    private utilsService: UtilsService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.subscriptions.add(
      this.notifications$.subscribe((notifications: AppNotification[]) => {
        this.notifications =
          notifications && notifications.length
            ? notifications.slice().sort((a, b) => this.utilsService.compare(a.receivedAt, b.receivedAt, false))
            : null;
        this.cdRef.markForCheck();
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  removeNotification(notification: AppNotification): void {
    if (!notification) {
      return;
    }
    this.store.dispatch(new RemoveNotification(notification));
  }

  removeAllNotifications(): void {
    this.store.dispatch(new RemoveAllNotifications());
    this.helperService.redirectTo('list');
  }

  onSortOption(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    const sort: Sort = {
      active: event.value,
      direction: this.sortDirectionType,
    };
    this.sortData(sort);
  }

  onSortDirection(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    this.sortDirectionType = event.value;
    const sort: Sort = {
      active: this.sortOption.value,
      direction: event.value,
    };
    this.sortData(sort);
  }

  sortData(sort: Sort): boolean {
    const data = this.notifications.slice();
    if (!sort.active || sort.direction === '') {
      this.notifications = data;
      return;
    }

    this.notifications = data.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      switch (sort.active) {
        case this.COLUMNS.TYPE:
          return this.utilsService.compare(a.type, b.type, isAsc);
        case this.COLUMNS.MESSAGE:
          return this.utilsService.compare(a.message, b.message, isAsc);
        case this.COLUMNS.RECEIVED:
          return this.utilsService.compare(a.receivedAt, b.receivedAt, isAsc);
        default:
          return 0;
      }
    });
  }
}
