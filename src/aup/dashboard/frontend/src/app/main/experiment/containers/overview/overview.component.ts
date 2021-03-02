/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef, TemplateRef } from '@angular/core';
import { Store, Select } from '@ngxs/store';
import { SelectedExperiment, Hyperparameters, BestScoreParam } from '../../store/experiment-state.model';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription, interval } from 'rxjs';
import { ProgressBarWidthPipe } from '../../../../shared/pipes';
import { Experiment } from '../../../../models/experiment.model';
import { Router, ActivatedRoute } from '@angular/router';
import { GetExperiment, GetHyperparameters, RefreshInterval } from '../../store/experiment.actions';
import { SnackbarService, UtilsService } from '../../../../shared/services';
import { startWith, map } from 'rxjs/operators';
import { MatTableDataSource } from '@angular/material/table';
import { ViewChild } from '@angular/core';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';
import { MatDialog } from '@angular/material/dialog';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-overview',
  templateUrl: './overview.component.html',
  styleUrls: ['./overview.component.scss'],
})
export class OverviewComponent implements OnInit, OnDestroy {
  @Select(ExperimentState.selectedExperiment) experiment$: Observable<SelectedExperiment>;
  @Select(ExperimentState.experiments) experiments$: Observable<Experiment[]>;
  @Select(ExperimentState.hyperparameters) hyperparameters$: Observable<Hyperparameters>;
  @Select(ExperimentState.refreshInterval) refreshInterval$: Observable<number>;
  @Select(ExperimentState.refreshingInterval) refreshingInterval$: Observable<boolean>;
  @Select(ExperimentState.loadingExperiment) loadingExperiment$: Observable<boolean>;

  @ViewChild('paginatorParams', { static: true }) paginatorParams: MatPaginator;
  @ViewChild(MatSort, { static: true }) sortParams: MatSort;
  @ViewChild('showDetailsDialog', { static: true }) showDetailsDialog: TemplateRef<any>;

  pageSize = 8;
  subscriptions: Subscription;
  experimentId: number;
  experimentData: SelectedExperiment;
  experimentIndex: number;
  progressBarWidth: number;
  refreshInterval: number;
  refreshIntervalSubscription: Subscription;
  showDetails = false;
  showDetailsDialogRef;

  readonly PARAM_COLUMNS = {
    NAME: 'NAME',
    VALUE: 'BEST VALUE',
    RANGE: 'RANGE',
    TYPE: 'TYPE',
  };
  displayedResourceColumns = [
    this.PARAM_COLUMNS.NAME,
    this.PARAM_COLUMNS.VALUE,
    this.PARAM_COLUMNS.RANGE,
    this.PARAM_COLUMNS.TYPE,
  ];
  dataSourceParams = new MatTableDataSource<BestScoreParam>();

  constructor(
    public dialog: MatDialog,
    readonly store: Store,
    readonly router: Router,
    private route: ActivatedRoute,
    private cdRef: ChangeDetectorRef,
    private snackbarService: SnackbarService,
    private utilsService: UtilsService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.subscriptions.add(
      this.route?.parent?.params.subscribe((params) => {
        this.experimentId = params['id'];
      })
    );
    this.subscriptions.add(
      this.experiment$.subscribe((experimentData: SelectedExperiment) => {
        this.dataSourceParams.data = [];
        this.dataSourceParams.paginator = null;
        this.dataSourceParams.sort = null;
        if (experimentData) {
          this.experimentData = experimentData;
          if (
            experimentData &&
            experimentData.bestScore &&
            experimentData.bestScore.params &&
            experimentData.bestScore.params.length
          ) {
            this.dataSourceParams.data = experimentData.bestScore.params.slice();
            this.dataSourceParams.paginator = this.paginatorParams;
            this.dataSourceParams.sort = this.sortParams;
            this.cdRef.markForCheck();
          }
          const progressBarWidthPipe = new ProgressBarWidthPipe();
          this.progressBarWidth = progressBarWidthPipe.transform({
            value: this.experimentData.jobStats.finished,
            maxValue: this.experimentData.jobStats.total,
          });
          this.cdRef.markForCheck();
        }
      })
    );
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
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.refreshIntervalSubscription.unsubscribe();
  }

  openDetails(): void {
    this.showDetailsDialogRef = this.dialog.open(this.showDetailsDialog, {
      width: '650px',
      data: null,
      panelClass: 'info-modal',
    });
    this.subscriptions.add(this.showDetailsDialogRef.afterClosed().subscribe());
  }

  async toggleExperiment(id: number): Promise<void> {
    if (!id) {
      return;
    }
    this.experimentId = id;
    this.store.dispatch(new GetExperiment(this.experimentId));
    this.store.dispatch(new GetHyperparameters(this.experimentId));
    await this.router.navigate([`experiment/${id}/overview`]);
  }

  refreshIntervalData(): Observable<any> {
    if (this.refreshInterval) {
      return interval(this.refreshInterval * 1000).pipe(
        startWith(0),
        map(() => {
          console.log('Fetching overview data...');
          this.refreshData();
        })
      );
    }
  }

  refreshData(): void {
    if (this.experimentId) {
      this.store.dispatch(new GetExperiment(this.experimentId));
      this.store.dispatch(new GetHyperparameters(this.experimentId));
    }
  }

  sortParamData(sort: Sort): boolean {
    const data = this.experimentData?.bestScore?.params.slice();
    if (!sort.active || sort.direction === '') {
      this.dataSourceParams.data = data;
      return;
    }

    this.dataSourceParams.data = data.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      switch (sort.active) {
        case this.PARAM_COLUMNS.NAME:
          return this.utilsService.compare(a.name, b.name, isAsc);
        case this.PARAM_COLUMNS.RANGE:
          return this.utilsService.compare(a.range, b.range, isAsc);
        case this.PARAM_COLUMNS.VALUE:
          return this.utilsService.compare(a.value, b.value, isAsc);
        case this.PARAM_COLUMNS.TYPE:
          return this.utilsService.compare(a.type, b.type, isAsc);
        default:
          return 0;
      }
    });
  }
}
