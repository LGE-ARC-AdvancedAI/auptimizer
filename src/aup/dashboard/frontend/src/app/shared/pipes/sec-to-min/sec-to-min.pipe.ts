import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'secToMin',
})
export class SecToMinPipe implements PipeTransform {
  transform(value: number): string {
    if (value > 0 && value > 60) {
      const hours = Math.floor(value / 60);
      if (value % 2 !== 0) {
        const minutes = value - hours * 60;
        return `${hours}min ${minutes}s`;
      } else {
        return `${hours}min`;
      }
    } else {
      return `${value}s`;
    }
  }
}
