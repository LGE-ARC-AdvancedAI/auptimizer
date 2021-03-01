import { NOTIFICATION_TYPE } from '../models/enum/notification-type.enum';

export interface AppStateModel {
  theme: Theme;
  themes: Theme[];
  dbUrl: string;
  notifications: AppNotification[];
  notificationExpiration: number; // Seconds
}

export interface Theme {
  name: string;
  icon: string;
}

export interface AppNotification {
  receivedAt: number;
  type: NOTIFICATION_TYPE;
  message: string;
}
