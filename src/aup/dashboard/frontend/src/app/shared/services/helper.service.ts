/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
/* eslint-disable @typescript-eslint/no-floating-promises */
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root',
})
export class HelperService {
  constructor(private router: Router) {}

  redirectTo(link: string, param?: any): void {
    if (link) {
      if (param) {
        this.router.navigate([link, param]);
      } else {
        this.router.navigate([link]);
      }
    }
  }
}
