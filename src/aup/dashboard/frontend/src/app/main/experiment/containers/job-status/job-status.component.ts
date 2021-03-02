/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/restrict-template-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
/* eslint-disable @typescript-eslint/no-unused-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, OnDestroy, ViewChild, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription, interval } from 'rxjs';
import { JobStatus, PlotlyScatterGraph } from '../../store/experiment-state.model';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { ActivatedRoute, Router } from '@angular/router';
import {
  GetJobStatus,
  GetExperimentHistory,
  RefreshInterval,
  ChangeJobsGraphForLabel,
} from '../../store/experiment.actions';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { AppState } from '../../../../appStore/app.store';
import { Theme } from '../../../../appStore/app-state.model';
import { SnackbarService, UtilsService } from '../../../../shared/services';
import { startWith, map } from 'rxjs/operators';
import { MatSelectChange } from '@angular/material/select';
import { Navigate } from '@ngxs/router-plugin';
import { PlotlyService } from 'angular-plotly.js';
import { GRAPH_COLORS } from '../../../../models/data/graph-colors.data';
import { FormControl } from '@angular/forms';
import { FirstLetterUppercasePipe } from '../../../../shared/pipes';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-job-status',
  templateUrl: './job-status.component.html',
  styleUrls: ['./job-status.component.scss'],
})
export class JobStatusComponent implements OnInit, OnDestroy {
  @Select(AppState.theme) theme$: Observable<Theme>;
  @Select(ExperimentState.jobs) jobs$: Observable<JobStatus[]>;
  @Select(ExperimentState.jobsGraphData) jobsGraphData$: Observable<PlotlyScatterGraph>;
  @Select(ExperimentState.jobsOptimizationGraphData) jobsOptimizationGraphData$: Observable<PlotlyScatterGraph>;
  @Select(ExperimentState.refreshInterval) refreshInterval$: Observable<number>;
  @Select(ExperimentState.refreshingInterval) refreshingInterval$: Observable<boolean>;
  @Select(ExperimentState.jobMultipleResulsLabels) jobMultipleResulsLabels$: Observable<string[]>;
  @Select(ExperimentState.jobMultipleResulsSelectedLabel) jobMultipleResulsSelectedLabel$: Observable<string>;

  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;
  @ViewChild(MatSort, { static: true }) sort: MatSort;

  jobs: JobStatus[];
  jobMultipleResulsLabels: string[];
  jobMultipleResulsSelectedLabel: string;
  experimentId: number;
  jobsGraphData: PlotlyScatterGraph;
  jobsOptimizationGraphData: PlotlyScatterGraph;
  pageSize = 10;
  subscriptions: Subscription;
  displayedColumns: string[] = [];
  displayedHyperparamsColumns: string[] = [];
  allColumns: string[] = [];
  columnsToDisplay: string[] = [];
  dataSource = new MatTableDataSource<any>();
  tableFullData: { name: string; value: string }[] = [];
  tableHyperparamsData: { name: string; value: string }[] = [];
  optimizationCurve = true;
  refreshInterval: number;
  refreshIntervalSubscription: Subscription;
  selectedCols: string[];
  chartWidth = 600;
  showInteractionGuide = false;
  theme: Theme;
  selectedLabel = new FormControl();
  yAxisLabel = 'score';

  public linePlot = {
    data: [],
    layout: {
      height: 540,
      showlegend: true,
      title: {
        text: 'Score',
        font: {
          family: 'Courier New, monospace',
          size: 24,
        },
        xref: 'paper',
        x: 0.05,
      },
      xaxis: {
        title: {
          text: 'x Axis',
          font: {
            family: 'Courier New, monospace',
            size: 18,
            color: '#7f7f7f',
          },
        },
      },
      yaxis: {
        title: {
          text: 'Y Axis',
          font: {
            family: 'Courier New, monospace',
            size: 18,
            color: '#7f7f7f',
          },
        },
      },
    },
    config: {
      displayModeBar: false,
      responsive: true,
      displaylogo: false,
      // modeBarButtonsToRemove: PLOTLY_HIDDEN_DISPLAYS,
      scrollZoom: true,
    },
  };

  constructor(
    readonly store: Store,
    private route: ActivatedRoute,
    readonly router: Router,
    private cdRef: ChangeDetectorRef,
    private snackbarService: SnackbarService,
    public plotlyService: PlotlyService,
    public utilsService: UtilsService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.subscriptions.add(
      this.route?.parent?.params.subscribe((params) => {
        this.experimentId = params['id'];
        this.selectedCols = [];
        this.allColumns = [];
        // if (this.experimentId) {
        //   this.store.dispatch(new GetJobStatus({ eid: this.experimentId }));
        //   this.optimizationCurve = false;
        // }
      })
    );
    this.subscriptions.add(
      this.jobs$.subscribe((jobs: JobStatus[]) => {
        if (jobs && jobs.length) {
          this.jobs = jobs;
          this.displayedColumns = Object.keys(this.jobs[0].tableData);
          if (!this.selectedCols || !this.selectedCols.length) {
            this.selectedCols = this.displayedColumns.slice();
          }
          this.displayedHyperparamsColumns = Object.keys(this.jobs[0].tableHyperParams);
          this.allColumns = this.displayedColumns.concat(this.displayedHyperparamsColumns);

          this.columnsToDisplay = this.selectedCols.slice();

          this.jobs.map((job: JobStatus) => {
            this.tableHyperparamsData.push(job.tableHyperParams);
            this.tableFullData.push(job.tableFullData);
          });
          // console.log('tableFullData: ', this.tableFullData);
          this.dataSource.data = this.tableFullData.slice();
          this.dataSource.paginator = this.paginator;
          this.dataSource.sort = this.sort;
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.jobsGraphData$.subscribe((jobsGraphData: PlotlyScatterGraph) => {
        if (jobsGraphData) {
          this.jobsGraphData = jobsGraphData;
          this.linePlot.data = [];
          this.linePlot.data = [this.jobsGraphData];
          // console.log('jobsGraphData: ', jobsGraphData);
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.jobsOptimizationGraphData$.subscribe((jobsOptimizationGraphData: PlotlyScatterGraph) => {
        if (jobsOptimizationGraphData) {
          // console.log('jobsOptimizationGraphData:', jobsOptimizationGraphData);
          this.jobsOptimizationGraphData = jobsOptimizationGraphData;
          this.linePlot.data.push(jobsOptimizationGraphData);
          // console.log('linePlot: ', this.linePlot.data);
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        if (theme) {
          this.theme = theme;
          this.toggleChartTheme();
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
    this.subscriptions.add(
      this.jobMultipleResulsLabels$.subscribe((jobMultipleResulsLabels: string[]) => {
        this.jobMultipleResulsLabels = jobMultipleResulsLabels;
        this.cdRef.markForCheck();
      })
    );
    this.subscriptions.add(
      this.jobMultipleResulsSelectedLabel$.subscribe((jobMultipleResulsSelectedLabel: string) => {
        this.jobMultipleResulsSelectedLabel = jobMultipleResulsSelectedLabel;
        this.selectedLabel.patchValue(jobMultipleResulsSelectedLabel);
        this.cdRef.markForCheck();
      })
    );
  }

  toggleChartTheme(): void {
    if (!this.theme) {
      return;
    }
    this.theme.name === 'dark'
      ? (this.linePlot.layout = this.changeDarkModeChart())
      : (this.linePlot.layout = this.changeLightModeChart());
    this.cdRef.markForCheck();
  }

  get exportedName() {
    return `jobStatus-${new Date().getTime() / 1000}`;
  }

  selectHyperparams(event: MatSelectChange): void {
    if (!event) {
      return;
    }
    this.selectedCols = event.value;
    this.dataSource.data = this.tableFullData.slice();
    this.selectedCols = this.pushColumnToEnd('start time', this.selectedCols);
    this.selectedCols = this.pushColumnToEnd('end time', this.selectedCols);
    if (this.selectedCols) {
      this.columnsToDisplay = this.selectedCols.slice();
    } else {
      this.columnsToDisplay = [];
    }
    this.cdRef.markForCheck();
  }

  pushColumnToEnd(columnName: string, array: string[]): string[] {
    if (!columnName || !array || !array.length) {
      return;
    }
    const foundIndex = array.findIndex((item) => {
      return item === columnName;
    });
    if (foundIndex !== -1) {
      array.splice(foundIndex, 1);
      array.push(columnName);
    }
    return array;
  }

  downloadGraph(): void {
    const graphDiv = this.plotlyService.getInstanceByDivId('jobStatus');
    this.plotlyService
      .getPlotly()
      .downloadImage(graphDiv, { format: 'png', width: '1000', height: '450', filename: 'jobStatus' });
  }

  toggleExperiment(event): void {
    if (!event) {
      return;
    }
    this.experimentId = event;
    this.cleanData();
    this.yAxisLabel = 'score';
    this.toggleChartTheme();
    this.store.dispatch(new ChangeJobsGraphForLabel(this.yAxisLabel)).subscribe(() => {
      this.store.dispatch(new GetJobStatus({ eid: this.experimentId }));
      if (this.optimizationCurve) {
        this.store.dispatch(new GetExperimentHistory({ eid: this.experimentId }));
      }
      // this.router.navigate([`experiment/${event}/job-status`]);
      this.store.dispatch(new Navigate([`experiment/${event}/job-status`]));
      this.cdRef.markForCheck();
    });
  }

  cleanData(): void {
    this.optimizationCurve = true;
    this.columnsToDisplay = [];
    this.displayedHyperparamsColumns = [];
    this.tableHyperparamsData = [];
    this.tableFullData = [];
  }

  refreshIntervalData(): Observable<any> {
    if (this.refreshInterval) {
      return interval(this.refreshInterval * 1000).pipe(
        startWith(0),
        map(() => {
          console.log('Fetching job status data...');
          this.refreshData();
        })
      );
    }
  }

  refreshData(): void {
    this.toggleChartTheme();
    if (this.experimentId) {
      this.tableHyperparamsData = [];
      this.tableFullData = [];
      this.store.dispatch(new GetJobStatus({ eid: this.experimentId })).subscribe(() => {
        if (this.optimizationCurve) {
          this.store.dispatch(new GetExperimentHistory({ eid: this.experimentId }));
        }
      });
    }
  }

  changeLightModeChart(): any {
    const flu = new FirstLetterUppercasePipe();
    return {
      colorway: GRAPH_COLORS,
      height: 540,
      // xaxis: {
      //   // tickformat: '.0f'
      // },
      showlegend: true,
      xaxis: {
        zeroline: false,
        title: {
          text: 'Number of jobs',
          font: {
            size: 18,
            color: '#7f7f7f',
          },
        },
      },
      yaxis: {
        zeroline: false,
        title: {
          text: flu.transform(this.yAxisLabel),
          font: {
            size: 18,
            color: '#7f7f7f',
          },
        },
      },
    };
  }

  changeDarkModeChart(): any {
    const flu = new FirstLetterUppercasePipe();
    return {
      colorway: GRAPH_COLORS,
      plot_bgcolor: '#424242',
      paper_bgcolor: '#424242',
      height: 540,
      // title: 'Score',
      showlegend: true,
      legend: {
        font: {
          color: '#ffffff',
        },
      },
      xaxis: {
        // tickformat: '.0f',
        title: {
          text: 'Number of jobs',
          font: {
            size: 18,
            color: '#ffffff',
          },
        },
        gridcolor: '#c0c0c0',
        tickfont: {
          color: '#ffffff',
        },
        showline: true,
        showgrid: true,
        zeroline: false,
        showticklabels: true,
      },
      yaxis: {
        title: {
          text: flu.transform(this.yAxisLabel),
          font: {
            size: 18,
            color: '#ffffff',
          },
        },
        gridcolor: '#c0c0c0',
        tickfont: {
          color: '#ffffff',
        },
        showline: true,
        showgrid: true,
        zeroline: false,
        showticklabels: true,
      },
      line: {
        color: '#ffffff',
      },
    };
  }

  onToggleChartLine(event: MatSlideToggleChange): void {
    if (!event) {
      return;
    }
    // this.jobsGraphData.mode = this.optimizationCurve ? 'lines+markers' : 'markers';
    switch (event.checked) {
      case true:
        this.store.dispatch(new GetExperimentHistory({ eid: this.experimentId }));
        break;
      case false:
        this.tableHyperparamsData = [];
        this.tableFullData = [];
        this.store.dispatch(new GetJobStatus({ eid: this.experimentId }));
        break;
    }
    this.cdRef.markForCheck();
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.refreshIntervalSubscription.unsubscribe();
  }

  onResize(event) {
    if (event) {
      this.cdRef.markForCheck();
    }
  }

  selectLabel(label: string): void {
    if (!label) {
      return;
    }
    this.yAxisLabel = label;
    this.cdRef.markForCheck();
    // this.optimizationCurve = false;
    this.toggleChartTheme();
    this.store.dispatch(new ChangeJobsGraphForLabel(label));
    if (this.optimizationCurve) {
      this.store.dispatch(new GetExperimentHistory({ eid: this.experimentId }));
    }
  }
}
