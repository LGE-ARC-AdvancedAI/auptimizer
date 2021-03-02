/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({ name: 'roundNumber' })
export class RoundNumberPipe implements PipeTransform {
  transform(value: any): number | string {
    if (value === null || value === undefined) {
      return 'no valid score so far...';
    }
    if (Number.isInteger(+value)) {
      return +value;
    }
    return Math.round((+value + Number.EPSILON) * 10000) / 10000;
  }
}
