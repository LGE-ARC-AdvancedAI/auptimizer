import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'minToHour',
})
export class MinToHourPipe implements PipeTransform {
  transform(value: number): string {
    if (value > 0 && value > 60) {
      const hours = Math.floor(value / 60);
      if (value % 2 !== 0) {
        const minutes = value - hours * 60;
        return `${hours}h ${minutes}min`;
      } else {
        return `${hours}h`;
      }
    } else {
      return `${value}min`;
    }
  }
}
