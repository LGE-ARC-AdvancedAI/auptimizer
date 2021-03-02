/* eslint-disable prefer-arrow/prefer-arrow-functions */
/* eslint-disable @typescript-eslint/prefer-for-of */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unused-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/unbound-method */
/* eslint-disable no-shadow */
/* eslint-disable @typescript-eslint/naming-convention */
import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription } from 'rxjs';
import { Experiment, ExperimentHistory } from '../../../../models/experiment.model';
import { Router, ActivatedRoute } from '@angular/router';
import { MatSelectChange } from '@angular/material/select';
import { FormControl } from '@angular/forms';
import { AppState } from '../../../../appStore/app.store';
import { Theme } from '../../../../appStore/app-state.model';
import { ExperimentService } from '../../services/experiment.service';
import { FirstLetterUppercasePipe } from '../../../../shared/pipes';
import { PlotlyService } from 'angular-plotly.js';
import { GRAPH_COLORS } from '../../../../models/data/graph-colors.data';

export enum AXIS_TYPE {
  JOBS = 'jobs',
  SCORE = 'score',
  TIME = 'time (seconds)',
}

export enum SORT_BY {
  JID = 'jid',
  END_TIME = 'end_time',
}

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-multi-exp-comp',
  templateUrl: './multi-exp-comp.component.html',
  styleUrls: ['./multi-exp-comp.component.scss'],
})
export class MultiExpCompComponent implements OnInit {
  @Select(ExperimentState.experiments) experiments$: Observable<Experiment[]>;
  @Select(ExperimentState.experimentsMultiplier) experimentsMultiplier$: Observable<number>;
  @Select(AppState.theme) theme$: Observable<Theme>;

  // experimentMultiplierForm: FormControl;
  experimentMultiplier = 1;
  subscriptions: Subscription;
  experiments: Experiment[];
  experimentId: number;
  xAxisType: FormControl;
  yAxisType: FormControl;
  axisValues = [AXIS_TYPE.JOBS, AXIS_TYPE.TIME];
  yAxisValue: string = AXIS_TYPE.SCORE;
  selectedExperiments: Experiment[] = [];
  checkedExperiments: Experiment[] = [];
  theme: Theme;
  SORT_BY = SORT_BY;
  selectedSortBy = SORT_BY.JID;
  stepSizes = [1, 2];
  commonLabels: string[] = [];
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

  constructor(
    readonly store: Store,
    readonly router: Router,
    private route: ActivatedRoute,
    private cdRef: ChangeDetectorRef,
    private experimentService: ExperimentService,
    private plotlyService: PlotlyService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    // this.experimentMultiplierForm = new FormControl(1, [Validators.required, Validators.pattern(/^-?([1-9]\d*)?$/)]);
    this.xAxisType = new FormControl(this.axisValues[0]);
    this.yAxisType = new FormControl(this.yAxisValue);
    this.subscriptions.add(
      this.route?.parent?.params.subscribe((params) => {
        this.experimentId = params['id'];
      })
    );
    this.subscriptions.add(
      this.experiments$.subscribe((experiments: Experiment[]) => {
        if (experiments && experiments.length > 0) {
          // this.store.dispatch(new GetExperimentsHistoryBest());
          this.getExperimentsBestHistory();
          if (!this.selectedExperiments.length) {
            this.experiments = experiments.slice();
          }
          this.computePlots();
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        if (theme) {
          this.theme = theme;
          this.provideLayoutBasedOnTheme();
        }
      })
    );
    this.subscriptions.add(
      this.experimentsMultiplier$.subscribe((multiplier: number) => {
        if (multiplier) {
          // this.experimentMultiplier = multiplier;
        }
      })
    );
    // this.experimentMultiplierForm.valueChanges.pipe(distinctUntilChanged()).subscribe((multiplier: number) => {
    //   if (multiplier) {
    //     this.experimentMultiplier = multiplier;
    //     this.getExperimentsBestHistory();
    //   }
    // });
  }

  provideLayoutBasedOnTheme(): void {
    this.graph.layout = this.changeLightModeChart();
    if (this.theme) {
      this.theme.name === 'dark'
        ? (this.graph.layout = this.changeDarkModeChart())
        : (this.graph.layout = this.changeLightModeChart());
      this.cdRef.markForCheck();
    }
  }

  downloadGraph(): void {
    const graphDiv = this.plotlyService.getInstanceByDivId('multiExperiment');
    this.plotlyService
      .getPlotly()
      .downloadImage(graphDiv, { format: 'png', width: '1000', height: '450', filename: 'multiExperiment' });
  }

  getExperimentsBestHistory(): void {
    if (!this.experimentMultiplier) {
      return;
    }
    const label = this.selectedLabel.value;
    this.experimentService
      .getAllExperimentHistoryBest(this.experimentMultiplier, this.selectedSortBy, label)
      .subscribe((res) => {
        if (res && res['experiment_history_best']) {
          const history = res['experiment_history_best'];
          this.experiments.map((exp) => {
            exp.history = [];
            if (history[exp.eid]) {
              history[exp.eid].map((expHistory) => {
                const experimentHistory: ExperimentHistory = {
                  jid: expHistory['jid'],
                  jobConfig: JSON.parse(expHistory['job_config']),
                  score: expHistory['score'],
                };
                exp.history.push(experimentHistory);
              });
            }
          });
          this.selectedExperiments.map((exp) => {
            exp.history = [];
            history[exp.eid].map((expHistory) => {
              const experimentHistory: ExperimentHistory = {
                jid: expHistory['jid'],
                jobConfig: JSON.parse(expHistory['job_config']),
                score: expHistory['score'],
              };
              exp.history.push(experimentHistory);
            });
          });
          this.computePlots();
          this.cdRef.markForCheck();
        }
      });
  }

  // get experimentMultiplierValue(): number {
  //   return this.experimentMultiplierForm.value;
  // }

  get xAxisValue(): AXIS_TYPE {
    return this.xAxisType.value;
  }

  changeLightModeChart(): any {
    const flu = new FirstLetterUppercasePipe();
    return {
      colorway: GRAPH_COLORS,
      hovermode: 'closest',
      height: 450,
      showlegend: true,
      // title: {
      //   text: 'Score',
      // },
      xaxis: {
        zeroline: false,
        title: {
          text: flu.transform(this.xAxisValue),
          font: {
            size: 18,
            color: '#7f7f7f',
          },
        },
      },
      yaxis: {
        zeroline: false,
        title: {
          text: flu.transform(this.yAxisValue),
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
          text: flu.transform(this.xAxisValue),
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
          text: flu.transform(this.yAxisValue),
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

  selectExperiment(event: MatSelectChange): void {
    const scoreLabel = 'score';
    if (!event.value) {
      return;
    }
    this.selectedExperiments = event.value;
    let combinedLabels = [];
    this.commonLabels = [];
    for (let i = 0; i < this.selectedExperiments.length; i++) {
      if (!this.selectedExperiments[i].labels || !this.selectedExperiments[i].labels.length) {
        combinedLabels = [];
        this.commonLabels = [];
        break;
      } else {
        combinedLabels.push(this.selectedExperiments[i].labels);
      }
    }
    if (combinedLabels.length) {
      if (combinedLabels.length > 1) {
        this.commonLabels = combinedLabels.shift().filter(function (v) {
          return combinedLabels.every(function (a) {
            return a.indexOf(v) !== -1;
          });
        });
        // if (!this.commonLabels.length) {
        //   this.selectedLabel.patchValue(scoreLabel);
        //   this.selectLabel(scoreLabel);
        // }
      } else {
        this.commonLabels = combinedLabels[0].slice();
      }
      this.commonLabels.length > 0 ? this.commonLabels.unshift(scoreLabel) : null;
    } else {
      this.commonLabels = [];
    }
    this.selectedLabel.patchValue(scoreLabel);
    this.selectLabel(scoreLabel);
    this.computePlots();
  }

  selectLabel(label: string): void {
    if (!label) {
      return;
    }
    this.yAxisValue = label;
    this.cdRef.markForCheck();
    this.getExperimentsBestHistory();
    this.computePlots();
  }

  changeXAxisValue(): void {
    switch (this.xAxisType.value) {
      case AXIS_TYPE.JOBS:
        this.selectedSortBy = SORT_BY.JID;
        break;
      case AXIS_TYPE.TIME:
        this.selectedSortBy = SORT_BY.END_TIME;
        break;
      default:
        this.selectedSortBy = null;
        break;
    }
    this.getExperimentsBestHistory();
    this.computePlots();
  }

  computePlots(): void {
    this.provideLayoutBasedOnTheme();
    if (this.selectedExperiments.length) {
      const traces = this.selectedExperiments.map((experiment: Experiment) => {
        return {
          x: [...this.computeXAxis(experiment)],
          y: [...this.computeYAxis(experiment)],
          // hovertext: [...this.computeHoverText(experiment)],
          mode: 'lines+markers',
          // marker: { size: 11 },
          type: 'scatter',
          name: experiment.experimentName ? experiment.experimentName : experiment.scriptName,
        };
      });
      this.graph.data = traces;
      this.cdRef.markForCheck();
    } else {
      this.graph.data = [];
    }
  }
  // computeHoverText(experiment: Experiment): any {
  //   if (this.xAxisType.value && experiment) {
  //     switch (this.xAxisType.value) {
  //       case AXIS_TYPE.JOBS:
  //         return experiment.jobs.map((job, index) => 'TEST1');
  //       case AXIS_TYPE.SCORE:
  //         return experiment.jobs.map((job, index) => 'TEST2');
  //     }
  //   }
  // }

  computeXAxis(experiment: Experiment): any {
    if (this.xAxisType.value && experiment) {
      switch (this.xAxisType.value) {
        case AXIS_TYPE.JOBS:
          return experiment.history.map((expHistory, index) => {
            const newIndex = this.experimentMultiplier * (index + 1);
            return newIndex - Math.floor(newIndex / experiment.jobs.length) * (newIndex % experiment.jobs.length);
          });
        case AXIS_TYPE.TIME:
          // console.log(
          //   'X AXIS: - TIME',
          //   experiment.jobs.map((job) => (job['end_time'] ? job['end_time'] - experiment.startTime : null))
          // );
          return experiment.jobs.map((job) => (job['end_time'] ? job['end_time'] - experiment.startTime : null));
      }
      this.cdRef.markForCheck();
    }
  }

  computeYAxis(experiment: Experiment): any {
    if (this.yAxisType.value && experiment) {
      return experiment.history.map((expHistory) => expHistory.score);
    }
    this.cdRef.markForCheck();
  }
}
