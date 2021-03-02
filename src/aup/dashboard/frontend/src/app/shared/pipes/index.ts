import { MinToHourPipe } from './min-to-hour/min-to-hour.pipe';
import { SecToMinPipe } from './sec-to-min/sec-to-min.pipe';
import { RoundNumberPipe } from './roudNumber.pipe';
import { ProgressBarWidthPipe } from './progressBarWidth.pipe';
import { FirstLetterUppercasePipe } from './first-letter-uppercase/first-letter-uppercase.pipe';
import { ExperimentStatusPipe } from './experiment-status.pipe';
import { NotificationIconPipe } from './notification-icon.pipe';
import { TruncatePipe } from './truncate.pipe';

export const pipes = [
  MinToHourPipe,
  SecToMinPipe,
  RoundNumberPipe,
  ProgressBarWidthPipe,
  FirstLetterUppercasePipe,
  ExperimentStatusPipe,
  NotificationIconPipe,
  TruncatePipe,
];

export * from './min-to-hour/min-to-hour.pipe';
export * from './sec-to-min/sec-to-min.pipe';
export * from './roudNumber.pipe';
export * from './progressBarWidth.pipe';
export * from './experiment-status.pipe';
export * from './first-letter-uppercase/first-letter-uppercase.pipe';
export * from './notification-icon.pipe';
