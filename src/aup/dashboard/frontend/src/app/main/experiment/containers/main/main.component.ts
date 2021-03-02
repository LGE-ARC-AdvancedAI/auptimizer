/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, OnDestroy } from '@angular/core';
import { Store, Select } from '@ngxs/store';
import { Subscription, Observable, interval } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import {
  GetExperimentInterimResults,
  GetExperiments,
  RefreshAll,
  RefreshInterval,
} from '../../store/experiment.actions';
import { ExperimentState } from '../../store/experiment.store';
import { startWith, map } from 'rxjs/operators';
import { SnackbarService } from '../../../../shared/services';
import { IntermediateExperiment } from '../../store/experiment-state.model';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss'],
})
export class MainComponent implements OnInit, OnDestroy {
  @Select(ExperimentState.refreshInterval) refreshInterval$: Observable<number>;
  @Select(ExperimentState.refreshingInterval) refreshingInterval$: Observable<boolean>;
  @Select(ExperimentState.interimExperiment) interimExperiment$: Observable<IntermediateExperiment>;

  subscriptions: Subscription;
  refreshIntervalSubscription: Subscription;
  refreshInterval: number;
  experimentId: number;
  interimExperiment: IntermediateExperiment;

  constructor(
    readonly store: Store,
    readonly route: ActivatedRoute,
    readonly router: Router,
    private snackbarService: SnackbarService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    // this.refreshIntervalSubscription = new Subscription();
    this.subscriptions.add(
      this.refreshInterval$.subscribe((rInterval: number) => {
        if (rInterval) {
          if (this.refreshIntervalSubscription && rInterval !== this.refreshInterval) {
            this.refreshIntervalSubscription.unsubscribe();
          }
          this.refreshInterval = rInterval;
          this.refreshIntervalSubscription = this.refreshIntervalData().subscribe();
        }
      })
    );
    this.subscriptions.add(
      this.refreshingInterval$.subscribe((refreshingInterval: boolean) => {
        if (refreshingInterval) {
          this.refreshData();
          const message = 'Data refreshed!';
          this.snackbarService.success(message);
          this.store.dispatch(new RefreshInterval(false));
        }
      })
    );
    this.subscriptions.add(
      this.interimExperiment$.subscribe((interimExperiment: IntermediateExperiment) => {
        if (interimExperiment) {
          this.interimExperiment = interimExperiment;
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    if (this.refreshIntervalSubscription) {
      this.refreshIntervalSubscription.unsubscribe();
    }
  }

  // In the tables, fetch that data, but here, fetch this data
  refreshIntervalData(): Observable<any> {
    if (this.refreshInterval) {
      return interval(this.refreshInterval * 1000).pipe(
        startWith(0),
        map(() => {
          console.log('Fetching data...');
          this.refreshData();
        })
      );
    }
  }

  refreshData(): void {
    this.store.dispatch(new GetExperiments());
    this.store.dispatch(new RefreshAll());
    if (this.interimExperiment) {
      this.store.dispatch(new GetExperimentInterimResults({ eid: this.interimExperiment.eid }));
    }
  }
}
