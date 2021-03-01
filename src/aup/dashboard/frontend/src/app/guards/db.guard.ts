/* eslint-disable @typescript-eslint/unbound-method */
import { Injectable, NgZone } from '@angular/core';
import { Router, CanActivate } from '@angular/router';
import { Store } from '@ngxs/store';
import { AppState } from '../appStore/app.store';
import { Navigate } from '@ngxs/router-plugin';

@Injectable()
export class DBGuard implements CanActivate {
  constructor(readonly ngZone: NgZone, readonly store: Store, readonly router: Router) {}

  canActivate(): boolean {
    const isDbUrl = this.store.selectSnapshot(AppState.isDbUrl);
    if (!isDbUrl) {
      this.store.dispatch(new Navigate(['/initialize']));
    }
    return isDbUrl;
  }

  canLoad(): boolean {
    const isDbUrl = this.store.selectSnapshot(AppState.isDbUrl);
    if (!isDbUrl) {
      this.store.dispatch(new Navigate(['/initialize']));
    }
    return isDbUrl;
  }
}
