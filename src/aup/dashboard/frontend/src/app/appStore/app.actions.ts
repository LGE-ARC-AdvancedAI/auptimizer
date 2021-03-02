import { Theme } from './app-state.model';
import { AppNotification } from './app-state.model';

export class SetTheme {
  static readonly type = '[Theme] Set theme';
}

export class ChangeTheme {
  static readonly type = '[Theme] Change theme';
  constructor(public payload: Theme) {}
}

export class GetDatabaseLink {
  static readonly type = '[Database] Get database link';
}

export class AddNotification {
  static readonly type = '[Notifications] Add notification';
  constructor(public payload: AppNotification) {}
}

export class RemoveNotification {
  static readonly type = '[Notifications] Remove notification';
  constructor(public payload: AppNotification) {}
}

export class GetNotifications {
  static readonly type = '[Notifications] Get notifications';
}

export class RemoveAllNotifications {
  static readonly type = '[Notifications] Remove notifications';
}
