/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription, Observable } from 'rxjs';
import { Store, Select } from '@ngxs/store';
import { ActivatedRoute, Router } from '@angular/router';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { NavItem } from '../../../../models/nav-items.model';
import { ExperimentState } from '../../store/experiment.store';
import { GetInterimResults } from '../../store/experiment.actions';

@Component({
  selector: 'app-experiment',
  templateUrl: './experiment.component.html',
  styleUrls: ['./experiment.component.scss'],
  animations: [
    trigger('sidenavVisibility', [
      state('false', style({ width: '75px' })),
      state('true', style({ width: '250px' })),
      transition('false => true', animate('200ms ease-in')),
      transition('true => false', animate('200ms ease-in')),
    ]),
    trigger('contentVisibility', [
      state('false', style({ marginLeft: '75px' })),
      state('true', style({ marginLeft: '250px' })),
      transition('false => true', animate('200ms ease-in')),
      transition('true => false', animate('200ms ease-in')),
    ]),
  ],
})
export class ExperimentComponent implements OnInit, OnDestroy {
  @Select(ExperimentState.refreshInterval) refreshInterval$: Observable<number>;
  @Select(ExperimentState.refreshingInterval) refreshingInterval$: Observable<boolean>;
  @Select(ExperimentState.sidenavOpen) sidenavOpen$: Observable<boolean>;
  @Select(ExperimentState.navItems) navItems$: Observable<any[]>;

  subscription: Subscription;
  experimentId: number;
  isSidenavOpen = true;
  sideNavElements: NavItem[];
  refreshInterval: number;

  constructor(readonly store: Store, readonly route: ActivatedRoute, readonly router: Router) {}

  ngOnInit(): void {
    this.subscription = new Subscription();
    this.subscription.add(
      this.navItems$.subscribe((navItems: NavItem[]) => {
        if (navItems && navItems.length) {
          this.sideNavElements = navItems;
        }
      })
    );
    this.store.dispatch(new GetInterimResults());
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
