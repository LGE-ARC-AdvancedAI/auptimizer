import { Pipe, PipeTransform } from '@angular/core';
import { NOTIFICATION_TYPE } from '../../models/enum/notification-type.enum';

@Pipe({ name: 'notifyIcon' })
export class NotificationIconPipe implements PipeTransform {
  transform(value: string): string {
    if (!value) {
      return;
    }
    switch (value) {
      case NOTIFICATION_TYPE.ERROR:
        return 'error';
      case NOTIFICATION_TYPE.INFO:
        return 'notification_important';
      case NOTIFICATION_TYPE.SUCCESS:
        return 'check_circle';
      case NOTIFICATION_TYPE.WARNING:
        return 'warning';
    }
  }
}
