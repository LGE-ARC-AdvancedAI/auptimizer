import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'progressWidth' })
export class ProgressBarWidthPipe implements PipeTransform {
  transform(info: { value: number; maxValue: number }): number {
    if (info === null) {
      return;
    }
    return Math.floor((info.value * 100) / info.maxValue);
  }
}
