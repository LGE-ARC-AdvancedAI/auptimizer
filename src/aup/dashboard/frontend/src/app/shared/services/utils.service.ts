/* eslint-disable prefer-rest-params */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import * as moment from 'moment';

@Injectable({
  providedIn: 'root',
})
export class UtilsService {
  dataToString(data): string {
    const momentData = moment(data);
    return momentData && momentData.isValid() ? momentData.format('YYYY-MM-DD') : '';
  }

  dataToStringWithFormat(data: any, format: string): string {
    const momentData = moment(data);
    return momentData && momentData.isValid() ? momentData.format(format) : '';
  }

  compare(a: number | string, b: number | string, isAsc: boolean): number {
    return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
  }

  toCamel(s: string): string {
    return s.replace(/([-_][a-z])/gi, ($1) => {
      return $1.toUpperCase().replace('-', '').replace('_', '');
    });
  }

  keysToCamel(o: any): any {
    if (o === Object(o) && !Array.isArray(o) && typeof o !== 'function') {
      const n = {};
      Object.keys(o).forEach((k) => {
        n[this.toCamel(k)] = this.keysToCamel(o[k]);
      });
      return n;
    } else if (Array.isArray(o)) {
      return o.map((i) => {
        return this.keysToCamel(i);
      });
    }
    return o;
  }

  formatErrorMessage(err: HttpErrorResponse): string {
    if (!err) {
      return;
    }
    return err.error ? err.error.message.toString() : err.message ? err.message.toString() : err.toString();
  }

  trimString(text: string): string {
    if (!text) {
      return text;
    }
    const query = text.toString().toLocaleLowerCase().trim();
    return query;
  }

  filterArraysBasedOnId(): any {
    const arr = [...arguments];
    return arr.shift().filter((y) => arr.every((x) => x.some((j) => j.id === y.id)));
  }

  isNumber(n): boolean {
    return typeof n === 'number' && !isNaN(n) && isFinite(n);
  }
}
