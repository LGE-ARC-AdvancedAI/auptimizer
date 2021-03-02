/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/no-unused-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-floating-promises */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/unbound-method */
// import { DatePipe, formatDate } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  LOCALE_ID,
  Inject,
} from '@angular/core';
import { MatSelectChange } from '@angular/material/select';
import { ActivatedRoute, Router } from '@angular/router';
import { Select, Store } from '@ngxs/store';
import { PlotlyService } from 'angular-plotly.js';
import { Observable, Subscription } from 'rxjs';
import { withLatestFrom } from 'rxjs/operators';
import { Theme } from '../../../../appStore/app-state.model';
import { AppState } from '../../../../appStore/app.store';
import { FirstLetterUppercasePipe } from '../../../../shared/pipes';
import { UtilsService } from '../../../../shared/services';
import { IntermediateExperiment, IntermediateJob, IntermediateResult } from '../../store/experiment-state.model';
import { GetExperimentInterimResults, SetInterimExperiment } from '../../store/experiment.actions';
import { ExperimentState } from '../../store/experiment.store';
import { GRAPH_COLORS } from '../../../../models/data/graph-colors.data';
import { FormControl } from '@angular/forms';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-interm-results',
  templateUrl: './interm-results.component.html',
  styleUrls: ['./interm-results.component.scss'],
})
export class IntermResultsComponent implements OnInit, OnDestroy {
  @Select(AppState.theme) theme$: Observable<Theme>;
  @Select(ExperimentState.intermResults) intermResults$: Observable<IntermediateExperiment[]>;
  @Select(ExperimentState.loadingIntermResults) loadingIntermResults$: Observable<boolean>;
  @Select(ExperimentState.interimExperimentJobs) interimExperimentJobs$: Observable<IntermediateJob[]>;
  @Select(ExperimentState.interimExperimentMultResLabels) interimExperimentMultResLabels$: Observable<string[]>;
  @Select(ExperimentState.interimExperimentSelectedLabel) interimExperimentSelectedLabel$: Observable<string>;

  subscriptions: Subscription;
  intermResults: IntermediateExperiment[];
  jobs: IntermediateJob[];
  theme: Theme;
  selectedExperiment: IntermediateExperiment;
  selectedJobs: IntermediateJob[] = [];
  interimExperimentMultResLabels: string[];
  selectedLabel = new FormControl();
  yAxisLabel = 'score';

  public graph = {
    data: [],
    layout: {
      height: 540,
      xaxis: {
        title: {
          text: '',
        },
      },
      yaxis: {
        title: {
          text: '',
        },
      },
    },
    config: {
      responsive: true,
      displayModeBar: false,
      scrollZoom: true,
    },
  };

  showInteractionGuide = false;
  experimentId: number;
  flag: boolean;

  constructor(
    @Inject(LOCALE_ID) private locale: string,
    readonly store: Store,
    private cdRef: ChangeDetectorRef,
    private route: ActivatedRoute,
    private utilsService: UtilsService,
    private plotlyService: PlotlyService,
    readonly router: Router
  ) {
    this.flag = true;
  }

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    if (this.route?.parent?.params) {
      this.subscriptions.add(
        this.intermResults$
          .pipe(withLatestFrom(this.route?.parent?.params))
          .subscribe(([intermResults, params]: [IntermediateExperiment[], any]) => {
            if (params && params['id']) {
              this.experimentId = params['id'];
            }
            if (intermResults && intermResults.length) {
              this.intermResults = intermResults;
              this.intermResults.map((exp: IntermediateExperiment) => {
                console.log(exp);
                // console.log(this.experimentId);
                if (exp.eid === +this.experimentId) {
                  this.selectedExperiment = exp;
                  console.log(this.selectedExperiment);
                  this.store.dispatch(new SetInterimExperiment(this.selectedExperiment));
                  this.store.dispatch(new GetExperimentInterimResults({ eid: this.selectedExperiment.eid }));
                  this.cdRef.markForCheck();
                }
              });
              this.cdRef.markForCheck();
            }
          })
      );
    }
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        if (theme) {
          this.theme = theme;
          this.toggleChartTheme();
        }
      })
    );
    this.subscriptions.add(
      this.interimExperimentMultResLabels$.subscribe((interimExperimentMultResLabels: string[]) => {
        this.interimExperimentMultResLabels = interimExperimentMultResLabels;
      })
    );
    this.subscriptions.add(
      this.interimExperimentSelectedLabel$.subscribe((interimExperimentSelectedLabel: string) => {
        if (interimExperimentSelectedLabel) {
          console.log('interimExperimentSelectedLabel: ', interimExperimentSelectedLabel);
          this.selectedLabel.patchValue(interimExperimentSelectedLabel);
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.interimExperimentJobs$.subscribe((jobs: IntermediateJob[]) => {
        if (jobs && jobs.length) {
          const preselectedJobs = this.selectedJobs;
          this.jobs = jobs.slice().sort((a, b) => this.utilsService.compare(a.jid, b.jid, true));
          if (!this.selectedJobs.length && this.flag) {
            if (this.jobs[0]) {
              this.selectedJobs.push(this.jobs[0]);
            }
            if (this.jobs[1]) {
              this.selectedJobs.push(this.jobs[1]);
            }
            if (this.jobs[2]) {
              this.selectedJobs.push(this.jobs[2]);
            }
            this.computePlots();
          } else {
            this.selectedJobs = this.jobs.filter((y) => preselectedJobs.some((j) => j.jid === y.jid));
          }
          this.selectedJobs = this.jobs.filter((job) => preselectedJobs.some((preJob) => preJob.jid === job.jid));
          this.cdRef.markForCheck();
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  onSelectExperiment(matSelect: MatSelectChange): void {
    if (!matSelect) {
      return;
    }
    this.flag = true;
    this.selectedJobs = [];
    this.graph.data = [];
    this.selectedExperiment = matSelect.value;
    this.jobs = null;
    this.store.dispatch(new SetInterimExperiment(this.selectedExperiment));
    this.store.dispatch(new GetExperimentInterimResults({ eid: this.selectedExperiment.eid }));
    this.router.navigate([`experiment/${this.selectedExperiment.eid}/interm`]);
    this.cdRef.markForCheck();
  }

  onOpenSelectJob(): void {
    this.flag = false;
    this.store.dispatch(new GetExperimentInterimResults({ eid: this.selectedExperiment.eid }));
  }

  onSelectJob(matSelect: MatSelectChange): void {
    if (!matSelect) {
      return;
    }
    this.selectedJobs = matSelect.value;
    this.computePlots();
  }

  downloadGraph(): void {
    const graphDiv = this.plotlyService.getInstanceByDivId('interim');
    this.plotlyService
      .getPlotly()
      .downloadImage(graphDiv, { format: 'png', width: '1000', height: '450', filename: 'intermediateResults' });
  }

  computePlots(): void {
    this.toggleChartTheme();
    if (this.selectedJobs.length) {
      const traces = this.selectedJobs.map((job: IntermediateJob) => {
        return {
          x: [
            ...job.interimResults.map(
              (jIr: IntermediateResult) =>
                // formatDate(jIr.receiveTime * 1000, 'yyyy-MM-dd hh:mm:ss', this.locale)
                (jIr.receiveTime - job.interimResults[0].receiveTime) / 1000
            ),
          ],
          y: [...job.interimResults.map((jIr: IntermediateResult) => jIr.score)],
          mode: 'lines+markers',
          type: 'scatter',
          name: job.jid,
        };
      });
      this.graph.data = traces;
    } else {
      this.graph.data = [];
    }
    this.cdRef.markForCheck();
  }

  toggleChartTheme(): void {
    if (!this.theme) {
      return;
    }
    this.theme.name === 'dark'
      ? (this.graph.layout = this.changeDarkModeChart())
      : (this.graph.layout = this.changeLightModeChart());
    this.cdRef.markForCheck();
  }

  changeLightModeChart(): any {
    const flu = new FirstLetterUppercasePipe();
    return {
      colorway: GRAPH_COLORS,
      hovermode: 'closest',
      height: 450,
      showlegend: true,
      xaxis: {
        zeroline: false,
        title: {
          text: flu.transform('time (seconds)'),
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
      hovermode: 'closest',
      plot_bgcolor: '#424242',
      paper_bgcolor: '#424242',
      height: 450,
      showlegend: true,
      legend: {
        font: {
          color: '#ffffff',
        },
      },
      xaxis: {
        title: {
          text: flu.transform('time (seconds)'),
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

  selectLabel(label: string): void {
    if (!label) {
      return;
    }
    this.yAxisLabel = label;
    this.cdRef.markForCheck();
    this.flag = true;
    this.selectedJobs = [];
    this.graph.data = [];
    this.jobs = null;
    this.toggleChartTheme();
    this.store.dispatch(new GetExperimentInterimResults({ eid: this.selectedExperiment.eid, label }));
  }
}
