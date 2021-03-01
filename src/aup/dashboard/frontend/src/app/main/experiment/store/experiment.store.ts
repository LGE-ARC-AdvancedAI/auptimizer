/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/restrict-template-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { throwError, Observable } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { State, Action, StateContext, Selector, Store } from '@ngxs/store';
import { Navigate } from '@ngxs/router-plugin';
import { HelperService } from '../../../shared/services/helper.service';
import { SnackbarService } from '../../../shared/services/snackbar.service';
import {
  GetExperiments,
  GetExperiment,
  GetHyperparameters,
  GetJobStatus,
  GetMetricVsHparams,
  SetRefreshInterval,
  GetExperimentHistory,
  StartExperiment,
  StopExperiment,
  SetupDatabase,
  CreateExperiment,
  RefreshInterval,
  ToggleSideNav,
  RefreshAll,
  GetInterimResults,
  DeleteExperiment,
  SetExperimentDisplayView,
  SetInterimExperiment,
  GetExperimentInterimResults,
  ChangeJobsGraphForLabel,
} from './experiment.actions';
import {
  ExperimentStateModel,
  SelectedExperiment,
  Hyperparameters,
  JobStatus,
  PlotlyScatterGraph,
  ParallelCoordinates,
  IntermediateExperiment,
  IntermediateJob,
} from './experiment-state.model';
import { ExperimentService } from '../services/experiment.service';
import { Experiment } from '../../../models/experiment.model';
import { Resource } from '../../../models/resource.model';
import { UtilsService } from '../../../shared/services';
import { FirstLetterUppercasePipe } from '../../../shared/pipes';
import { AddNotification, GetDatabaseLink } from '../../../appStore/app.actions';
import { NavItem } from '../../../models/nav-items.model';
import { NAV_ITEMS } from '../../../models/data/nav-items';
import { AppNotification } from '../../../appStore/app-state.model';
import { NOTIFICATION_TYPE } from '../../../models/enum/notification-type.enum';
import { EXPERIMENT_VIEW_TYPE } from '../../../models/enum/experiment-view-type.enum';
import { TruncatePipe } from '../../../shared/pipes/truncate.pipe';

@State<ExperimentStateModel>({
  name: 'experiment',
  defaults: {
    experiments: [],
    firstValidJobNumber: null,
    intermResults: null,
    interimExperiment: null,
    experimentsMultiplier: 1,
    resources: [],
    selectedExperiment: null,
    hyperparameters: null,
    jobStatusSortCriteria: {
      sortby: 'jid',
      asc: 1,
    },
    jobs: [],
    jobsGraphData: null,
    jobsOptimizationGraphData: null,
    jobsMultipleResults: {
      labels: [],
      selectedLabel: null,
    },
    jobsMultiplier: 1,
    metricsVsHparams: null,
    parallelCoordinatesTrace: null,
    refreshIntervalOptions: [5, 10, 30, 60],
    refreshInterval: 60,
    refreshingInterval: false,
    sidenavOpen:
      localStorage.getItem('sidenavOpen') !== null && localStorage.getItem('sidenavOpen') !== undefined
        ? JSON.parse(localStorage.getItem('sidenavOpen'))
        : true,
    navItems: NAV_ITEMS,
    loadingExperiment: false,
    loadingAllExperiments: false,
    loadingIntermResults: false,
    experimentViewType:
      (localStorage.getItem('experimentViewType') as EXPERIMENT_VIEW_TYPE) || EXPERIMENT_VIEW_TYPE.LIST,
  },
})
@Injectable()
export class ExperimentState {
  constructor(
    readonly service: ExperimentService,
    readonly helperService: HelperService,
    readonly snackbarService: SnackbarService,
    readonly utilsService: UtilsService,
    readonly store: Store
  ) {}

  @Selector()
  static loadingExperiment(state: ExperimentStateModel): boolean {
    return state.loadingExperiment;
  }

  @Selector()
  static loadingAllExperiments(state: ExperimentStateModel): boolean {
    return state.loadingAllExperiments;
  }

  @Selector()
  static loadingIntermResults(state: ExperimentStateModel): boolean {
    return state.loadingIntermResults;
  }

  @Selector()
  static experimentsMultiplier(state: ExperimentStateModel): number {
    return state.experimentsMultiplier;
  }

  @Selector()
  static refreshInterval(state: ExperimentStateModel): number {
    return state.refreshInterval;
  }

  @Selector()
  static refreshIntervalOptions(state: ExperimentStateModel): number[] {
    return state.refreshIntervalOptions;
  }

  @Selector()
  static refreshingInterval(state: ExperimentStateModel): boolean {
    return state.refreshingInterval;
  }

  @Selector()
  static experiments(state: ExperimentStateModel): Experiment[] {
    return state.experiments;
  }

  @Selector()
  static selectedExperiment(state: ExperimentStateModel): SelectedExperiment {
    return state.selectedExperiment;
  }

  @Selector()
  static resources(state: ExperimentStateModel): Resource[] {
    return state.resources;
  }

  @Selector()
  static hyperparameters(state: ExperimentStateModel): Hyperparameters {
    return state.hyperparameters;
  }

  @Selector()
  static metricsVsHparams(state: ExperimentStateModel): any {
    return state.metricsVsHparams;
  }

  @Selector()
  static parallelCoordinatesTrace(state: ExperimentStateModel): ParallelCoordinates {
    return state.parallelCoordinatesTrace;
  }

  @Selector()
  static jobs(state: ExperimentStateModel): JobStatus[] {
    return state.jobs;
  }

  @Selector()
  static jobMultipleResulsLabels(state: ExperimentStateModel): string[] {
    return state.jobsMultipleResults.labels;
  }

  @Selector()
  static jobMultipleResulsSelectedLabel(state: ExperimentStateModel): string {
    return state.jobsMultipleResults.selectedLabel;
  }

  @Selector()
  static jobsGraphData(state: ExperimentStateModel): PlotlyScatterGraph {
    return state.jobsGraphData;
  }

  @Selector()
  static jobsOptimizationGraphData(state: ExperimentStateModel): PlotlyScatterGraph {
    return state.jobsOptimizationGraphData;
  }

  @Selector()
  static sidenavOpen(state: ExperimentStateModel): boolean {
    return state.sidenavOpen;
  }

  @Selector()
  static intermResults(state: ExperimentStateModel): IntermediateExperiment[] | null {
    return state.intermResults;
  }

  @Selector()
  static interimExperiment(state: ExperimentStateModel): IntermediateExperiment {
    return state.interimExperiment;
  }

  @Selector()
  static interimExperimentJobs(state: ExperimentStateModel): IntermediateJob[] {
    return state.interimExperiment.jobs;
  }

  @Selector()
  static interimExperimentMultResLabels(state: ExperimentStateModel): string[] {
    return state.interimExperiment.multResLabels;
  }

  @Selector()
  static interimExperimentSelectedLabel(state: ExperimentStateModel): string {
    return state.interimExperiment.selectedLabel;
  }

  @Selector()
  static navItems(state: ExperimentStateModel): NavItem[] {
    return state.navItems;
  }

  @Selector()
  static experimentViewType(state: ExperimentStateModel): EXPERIMENT_VIEW_TYPE {
    return state.experimentViewType;
  }

  @Action(ToggleSideNav)
  toggleSideNav(ctx: StateContext<ExperimentStateModel>): Observable<any> {
    const state = ctx.getState();
    localStorage.setItem('sidenavOpen', JSON.stringify(!state.sidenavOpen));
    ctx.patchState({
      sidenavOpen: !state.sidenavOpen,
    });
    return;
  }

  @Action(SetRefreshInterval)
  setRefreshInterval(ctx: StateContext<ExperimentStateModel>, { payload }: SetRefreshInterval): Observable<any> {
    if (!payload) {
      return;
    }
    ctx.patchState({
      refreshInterval: payload,
    });
    return;
  }

  @Action(SetExperimentDisplayView)
  setExperimentDisplayView(
    ctx: StateContext<ExperimentStateModel>,
    { payload }: SetExperimentDisplayView
  ): Observable<any> {
    if (!payload) {
      return;
    }
    localStorage.setItem('experimentViewType', payload);
    ctx.patchState({
      experimentViewType: payload,
    });
    return;
  }

  @Action(RefreshInterval)
  refreshInterval(ctx: StateContext<ExperimentStateModel>, { payload }: RefreshInterval): Observable<any> {
    ctx.patchState({
      refreshingInterval: payload,
    });
    return;
  }

  @Action(GetExperiments)
  getExperiments(ctx: StateContext<ExperimentStateModel>): Observable<any> {
    ctx.patchState({
      loadingAllExperiments: true,
    });
    const currentExperiments = ctx.getState().experiments;
    return this.service.getExperiments().pipe(
      catchError((err: HttpErrorResponse) => {
        ctx.patchState({
          loadingAllExperiments: false,
        });
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res) {
          const experiments = [];
          res.experiment.map((experiment: any) => {
            const newExperiment = {
              ...(this.utilsService.keysToCamel(experiment) as Experiment),
              scores: JSON.parse(experiment['scores']),
              jobs: JSON.parse(experiment['jobs']),
              expConfigDetails: JSON.parse(experiment['exp_config']),
            };
            if (currentExperiments.length) {
              currentExperiments.map((currentExperiment: Experiment) => {
                if (currentExperiment.eid === newExperiment.eid && currentExperiment.status !== newExperiment.status) {
                  const message = `Experiment ${newExperiment.experimentName} changed status from ${currentExperiment.status} to ${newExperiment.status}`;
                  const notification: AppNotification = {
                    type: NOTIFICATION_TYPE.INFO,
                    receivedAt: new Date().getTime(),
                    message,
                  };
                  this.store.dispatch(new AddNotification(notification));
                  this.snackbarService.info(message);
                }
              });
            }
            return experiments.push(newExperiment);
          });
          const sortedExperiments = experiments.slice().sort((a, b) => this.utilsService.compare(a.eid, b.eid, false));
          // console.log('sortedExperiments: ', sortedExperiments);
          ctx.patchState({
            experiments: sortedExperiments,
            resources: res.resource || [],
            loadingAllExperiments: false,
          });
        }
      })
    );
  }

  @Action(GetExperiment)
  getExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: GetExperiment): Observable<any> {
    if (!payload) {
      return;
    }
    ctx.patchState({
      loadingExperiment: true,
      selectedExperiment: null,
    });
    return this.service.getExperiment(payload).pipe(
      catchError((err: HttpErrorResponse) => {
        ctx.patchState({
          loadingExperiment: false,
        });
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res) {
          const experimentRes = this.utilsService.keysToCamel(res) as SelectedExperiment;
          const selectedExperiment: SelectedExperiment = {
            bestScore: experimentRes.bestScore,
            experiment: experimentRes.experiment,
            jobStats: experimentRes.jobStats,
          };
          // const sortedScoreParams = {};
          // Object.keys(selectedExperiment.bestScore)
          //   .sort()
          //   .forEach((key) => (sortedScoreParams[key] = selectedExperiment.bestScore[key]));
          // selectedExperiment.bestScore = sortedScoreParams;
          if (selectedExperiment.bestScore && selectedExperiment.bestScore.configList) {
            const configList = JSON.parse(selectedExperiment.bestScore.configList);
            selectedExperiment.bestScore.configList = configList;
          }
          const config = JSON.parse(selectedExperiment.experiment.expConfig);
          selectedExperiment.experiment.expConfig = config;
          ctx.patchState({
            selectedExperiment,
            loadingExperiment: false,
          });
        }
      })
    );
  }

  @Action(GetHyperparameters)
  getHyperparameters(ctx: StateContext<ExperimentStateModel>, { payload }: GetHyperparameters): Observable<any> {
    if (!payload) {
      return;
    }
    return this.service.getHyperparameters(payload).pipe(
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res) {
          const hyperparamsRes = this.utilsService.keysToCamel(res['exp_config']) as Hyperparameters;
          const params = JSON.parse(hyperparamsRes.parameters);
          hyperparamsRes.parameters = params.sort((a, b) => this.utilsService.compare(a.name, b.name, true));
          ctx.patchState({
            hyperparameters: hyperparamsRes,
          });
        }
      })
    );
  }

  @Action(GetJobStatus)
  getJobStatus(ctx: StateContext<ExperimentStateModel>, { payload }: GetJobStatus): Observable<any> {
    const state = ctx.getState();
    const selectedLabel = state.jobsMultipleResults.selectedLabel || 'score';

    if (!payload.eid) {
      return;
    }
    const sortCriteria = payload.sortCriteria || state.jobStatusSortCriteria;
    return this.service.getJobsStatus(payload.eid, sortCriteria).pipe(
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res && res['job']) {
          let labels = [];
          const flu = new FirstLetterUppercasePipe();
          if (res['mult_res_labels']) {
            labels = res['mult_res_labels'];
            labels.push('score');
          }
          const jobs = [];
          const jobsGraphData = {
            x: [],
            y: [],
            hovertext: [],
            hoverinfo: 'text',
            type: 'scatter',
            mode: 'markers',
            name: flu.transform(selectedLabel),
            line: {
              color: '#3DDF7E',
            },
          };
          const truncate = new TruncatePipe();
          let hoverText: string;
          let jobNumber = 1;
          let firstValidJobNumber = null;
          res['job'].map((job: any) => {
            const newJob = this.utilsService.keysToCamel(job) as JobStatus;
            newJob.tableData = {};
            newJob.tableHyperParams = {};
            newJob.tableFullData = {};
            newJob.tableData['job ID'] = newJob.jid;
            newJob.tableFullData['job ID'] = newJob.jid;
            newJob.tableData['resource ID'] = newJob.rid;
            newJob.tableFullData['resource ID'] = newJob.rid;
            newJob.tableData['status'] = flu.transform(newJob.status);
            newJob.tableFullData['status'] = flu.transform(newJob.status);
            newJob.tableData['score'] = newJob.score;
            newJob.tableFullData['score'] = newJob.score;
            newJob.tableData['start time'] = newJob.startTime;
            newJob.tableFullData['start time'] = newJob.startTime;
            newJob.tableData['end time'] = newJob.endTime;
            newJob.tableFullData['end time'] = newJob.endTime;
            if (selectedLabel) {
              if (job[selectedLabel] !== null && job[selectedLabel] !== undefined) {
                hoverText = `${flu.transform(selectedLabel)} ${job[selectedLabel]}<br>`;
                hoverText += `Job ID: ${job.jid}<br>`;
                jobsGraphData.x.push(jobNumber);
                jobsGraphData.y.push(job[selectedLabel]);
                if (firstValidJobNumber === null && this.utilsService.isNumber(job[selectedLabel])) {
                  firstValidJobNumber = jobNumber;
                }
                jobNumber++;
              }
            } else if (newJob.score !== null && newJob.score !== undefined) {
              hoverText = `${selectedLabel}: ${newJob.score}<br>`;
              hoverText += `Job ID: ${newJob.jid}<br>`;
              jobsGraphData.x.push(jobNumber);
              jobsGraphData.y.push(newJob.score);
              if (firstValidJobNumber === null && this.utilsService.isNumber(newJob.score)) {
                firstValidJobNumber = jobNumber;
              }
              jobNumber++;
            }
            const config = JSON.parse(job['job_config']);
            newJob.jobConfig = config;
            Object.entries(newJob.jobConfig).map((object) => {
              newJob.tableFullData[`${object[0]}`] = object[1];
              newJob.tableHyperParams[`${object[0]}`] = object[1];
              if (newJob.score !== null && newJob.score !== undefined) {
                hoverText += `${flu.transform(truncate.transform(object[0], [100, '...']))}: ${object[1]}<br>`;
              }
            });
            if (labels.length) {
              labels.map((label: string) => {
                if (
                  label !== 'score' &&
                  !Object.keys(newJob.tableFullData).includes(label) &&
                  !Object.keys(newJob.tableHyperParams).includes(label)
                ) {
                  newJob.tableFullData[label] = newJob[label];
                  newJob.tableHyperParams[label] = newJob[label];
                }
              });
            }
            if (newJob.score !== null && newJob.score !== undefined) {
              jobsGraphData.hovertext.push(hoverText);
            }
            return jobs.push(newJob);
          });
          ctx.patchState({
            jobs,
            jobsGraphData,
            firstValidJobNumber,
            jobsMultipleResults: {
              ...state.jobsMultipleResults,
              labels,
              selectedLabel: selectedLabel || (labels && labels.length ? labels[labels.length - 1] : null),
            },
          });
          return;
        }
      })
    );
  }

  @Action(ChangeJobsGraphForLabel)
  changeJobsGraphForLabel(
    ctx: StateContext<ExperimentStateModel>,
    { payload }: ChangeJobsGraphForLabel
  ): Observable<any> {
    const state = ctx.getState();
    const flu = new FirstLetterUppercasePipe();
    if (!payload) {
      return;
    }
    const jobs = state.jobs;
    const jobsGraphData = {
      x: [],
      y: [],
      hovertext: [],
      hoverinfo: 'text',
      type: 'scatter',
      mode: 'markers',
      name: flu.transform(payload),
      line: {
        color: '#3DDF7E',
      },
    };
    const truncate = new TruncatePipe();
    let hoverText: string;
    let jobNumber = 1;
    let firstValidJobNumber = null;
    jobs.map((job) => {
      if (job[payload] !== null && job[payload] !== undefined) {
        hoverText = `${flu.transform(payload)} ${job[payload]}<br>`;
        hoverText += `Job ID: ${job.jid}<br>`;
        jobsGraphData.x.push(jobNumber);
        jobsGraphData.y.push(job[payload]);
        if (firstValidJobNumber === null && this.utilsService.isNumber(job[payload])) {
          firstValidJobNumber = jobNumber;
        }
        jobNumber++;
      }
      Object.entries(job.jobConfig).map((object) => {
        if (job[payload] !== null && job[payload] !== undefined) {
          hoverText += `${flu.transform(truncate.transform(object[0], [100, '...']))}: ${object[1]}<br>`;
        }
      });
      if (job[payload] !== null && job[payload] !== undefined) {
        jobsGraphData.hovertext.push(hoverText);
      }
      ctx.patchState({
        jobsGraphData,
        firstValidJobNumber,
        jobsMultipleResults: {
          ...state.jobsMultipleResults,
          selectedLabel: payload,
        },
      });
      return;
    });
  }

  @Action(GetExperimentHistory)
  getExperimentHistory(ctx: StateContext<ExperimentStateModel>, { payload }: GetExperimentHistory): Observable<any> {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    const multiplier = payload.n || state.jobsMultiplier;
    const sortBy = payload.sortby || 'jid';
    const label = state.jobsMultipleResults.selectedLabel;
    return this.service.getExperimentHistoryBest(payload.eid, multiplier, sortBy, label).pipe(
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res && res['experiment_history_best'] && res['experiment_history_best'].length) {
          const jobsOptimizationGraphData = {
            x: [],
            y: [],
            hovertext: [],
            hoverinfo: 'text',
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Best Results',
            line: {
              color: '#f44336',
            },
          };
          const flu = new FirstLetterUppercasePipe();
          const truncate = new TruncatePipe();
          let hoverText;
          const optimizationX = [];
          const selectedLabel = state.jobsMultipleResults.selectedLabel || 'score';

          let jobNumber = state.firstValidJobNumber;
          res['experiment_history_best'].map((history) => {
            hoverText = `${flu.transform(selectedLabel)}: ${history['score']}<br>`;
            hoverText += `Job ID: ${history['jid']}<br>`;
            // jobsOptimizationGraphData.x.push(multiplier * (index + 1));
            if (history['score'] !== null && history['score'] !== undefined) {
              optimizationX.push(jobNumber);
              jobsOptimizationGraphData.y.push(history['score']);
              jobNumber++;
            }
            const config = JSON.parse(history['job_config']);
            Object.entries(config).map((object) => {
              hoverText += `${flu.transform(truncate.transform(object[0], [100, '...']))}: ${object[1]}<br>`;
            });
            jobsOptimizationGraphData.hovertext.push(hoverText);
          });
          // for (let index = 0; index < state.firstValidJobNumber; index++) {
          //   optimizationX.pop();
          // }
          if (state.jobsGraphData && state.jobsGraphData.x.length) {
            const lastElementFromOptimization = optimizationX[optimizationX.length - 1];
            const jobsXData = optimizationX.slice();
            const foundIndex = jobsXData.findIndex((item) => item === lastElementFromOptimization);
            if (foundIndex !== -1) {
              const everythingAfterNumberInOptimization = jobsXData.slice(foundIndex);
              const positionInJobXData = jobsXData.indexOf(lastElementFromOptimization);
              jobsXData.splice(positionInJobXData);
              const newXData = jobsXData.concat(everythingAfterNumberInOptimization);
              jobsOptimizationGraphData.x = newXData;
            } else {
              jobsOptimizationGraphData.x = optimizationX;
            }
          } else {
            jobsOptimizationGraphData.x = optimizationX;
          }
          ctx.patchState({
            jobsOptimizationGraphData,
            jobsMultiplier: multiplier,
          });
          return;
        }
      })
    );
  }

  // @Action(GetExperimentsHistoryBest)
  // getExperimentsHistoryBest(ctx: StateContext<ExperimentStateModel>, { payload }: GetExperimentsHistoryBest): Observable<any> {
  //   const state = ctx.getState();
  //   const multiplier = payload || state.experimentsMultiplier;
  //   return this.service.getAllExperimentHistoryBest(multiplier).pipe(
  //     catchError((err: HttpErrorResponse) => {
  //       this.snackbarService.error(this.utilsService.formatErrorMessage(err));
  //       return throwError(err);
  //     }),
  //     map((res: any) => {
  //       if (res && res['experiment_history_best']) {
  //         const experimentsWithHistory = state.experiments;
  //         const history = res['experiment_history_best'];
  //         experimentsWithHistory.map(exp => {
  //           exp.history = [];
  //           history[exp.eid].map(expHistory => {
  //             const experimentHistory: ExperimentHistory = {
  //               jid: expHistory['jid'],
  //               jobConfig: JSON.parse(expHistory['job_config']),
  //               score: expHistory[score'],
  //             };
  //             exp.history.push(experimentHistory);
  //           });
  //         });
  //         ctx.patchState({
  //           experiments: experimentsWithHistory,
  //           experimentsMultiplier: multiplier
  //         });
  //       }
  //     })
  //   );
  // }

  @Action(GetMetricVsHparams)
  getMetricVsHparams(ctx: StateContext<ExperimentStateModel>, { payload }: GetMetricVsHparams): Observable<any> {
    if (!payload) {
      return;
    }
    return this.service.getMetricsVsHparams(payload).pipe(
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      }),
      map((res: any) => {
        if (res && res['metrics_vs_hparams']) {
          const metricsVsHparams = this.utilsService.keysToCamel(res['metrics_vs_hparams']);
          if (metricsVsHparams && metricsVsHparams.length > 0) {
            metricsVsHparams.sort((a, b) => (a.score > b.score ? 1 : -1));
            const dimensions = [];
            Object.keys(metricsVsHparams[0])
              .reverse()
              .map((key) =>
                dimensions.push({
                  label: key,
                  values: [],
                })
              );
            // if (state.selectedExperiment && state.selectedExperiment.experiment.expConfig.target) {
            //   // need to order it based on exp_config - target
            //   console.log(state.selectedExperiment.experiment.expConfig);
            // }
            const colors = metricsVsHparams.map((object) => (isNaN(object.score) ? 0 : object.score));
            metricsVsHparams.map((object) => {
              dimensions.map((dimension) => {
                if (dimension.label === 'score' && isNaN(object[dimension.label])) {
                  return dimension.values.push(0);
                }
                return dimension.values.push(object[dimension.label]);
              });
            });
            const trace: ParallelCoordinates = {
              type: 'parcoords',
              line: {
                showscale: true,
                reversescale: true,
                colorscale: 'Jet',
                cmin: metricsVsHparams[0].score,
                cmax: metricsVsHparams[metricsVsHparams.length - 1].score,
                color: colors,
              },
              dimensions,
            };
            ctx.patchState({
              metricsVsHparams,
              parallelCoordinatesTrace: trace,
            });
          } else {
            ctx.patchState({
              metricsVsHparams,
              parallelCoordinatesTrace: null,
            });
          }
        }
      })
    );
  }

  @Action(StartExperiment)
  startExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: StartExperiment): Observable<any> {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    return this.service.startExperiment(payload).pipe(
      tap((res: Experiment) => {
        if (res) {
          const experiments = state.experiments.slice();
          let experimentRes = this.utilsService.keysToCamel(res) as Experiment;
          experimentRes = {
            ...experimentRes,
            expConfigDetails: JSON.parse(experimentRes.expConfig),
          };
          const foundIndex = experiments.findIndex((item) => item.eid === experimentRes.eid);
          if (foundIndex !== -1) {
            experiments[foundIndex] = experimentRes;
          }
          ctx.patchState({
            experiments,
          });
          const message = 'Experiment started!';
          const notification: AppNotification = {
            type: NOTIFICATION_TYPE.SUCCESS,
            receivedAt: new Date().getTime(),
            message,
          };
          this.store.dispatch(new AddNotification(notification));
          this.snackbarService.success(message);
        }
        return;
      }),
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(StopExperiment)
  stopExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: StopExperiment): Observable<any> {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    return this.service.stopExperiment(payload).pipe(
      tap((res: Experiment) => {
        if (res) {
          const experiments = state.experiments.slice();
          let experimentRes = this.utilsService.keysToCamel(res) as Experiment;
          experimentRes = {
            ...experimentRes,
            expConfigDetails: JSON.parse(experimentRes.expConfig),
          };
          const foundIndex = experiments.findIndex((item) => item.eid === experimentRes.eid);
          if (foundIndex !== -1) {
            experiments[foundIndex] = experimentRes;
          }
          ctx.patchState({
            experiments,
          });
          const message = 'Experiment stopped!';
          const notification: AppNotification = {
            type: NOTIFICATION_TYPE.SUCCESS,
            receivedAt: new Date().getTime(),
            message,
          };
          this.store.dispatch(new AddNotification(notification));
          this.snackbarService.success(message);
          return;
        }
      }),
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(SetupDatabase)
  setupDatabase(ctx: StateContext<ExperimentStateModel>, { payload }: SetupDatabase): Observable<any> {
    if (!payload) {
      return;
    }
    return this.service.setupDB(payload).pipe(
      tap((res) => {
        if (res) {
          this.snackbarService.success('Setup completed');
          this.store.dispatch(new GetDatabaseLink()).subscribe(() => {
            this.store.dispatch(new Navigate(['/list']));
          });
        }
        return;
      }),
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(GetInterimResults)
  getInterimResults(ctx: StateContext<ExperimentStateModel>): Observable<any> {
    const state = ctx.getState();
    ctx.patchState({
      loadingIntermResults: true,
    });
    return this.service.getInterimResults().pipe(
      tap((intermResults: IntermediateExperiment[]) => {
        if (intermResults && intermResults.length) {
          ctx.patchState({
            intermResults,
            loadingIntermResults: false,
          });
        } else {
          const navItems = state.navItems.slice();
          const foundIndex = navItems.findIndex((el: NavItem) => el.route === 'interm');
          if (foundIndex !== -1) {
            navItems[foundIndex].disabled = true;
          }
          ctx.patchState({
            navItems,
            loadingIntermResults: false,
          });
        }
      }),
      catchError((err: HttpErrorResponse) => {
        ctx.patchState({
          loadingIntermResults: false,
        });
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(GetExperimentInterimResults)
  getExperimentInterimResults(
    ctx: StateContext<ExperimentStateModel>,
    { payload }: GetExperimentInterimResults
  ): Observable<any> {
    if (!payload) {
      return;
    }
    const state = ctx.getState();
    const selectedLabel = payload.label || state.interimExperiment.selectedLabel;
    if (state.intermResults && state.intermResults.length) {
      return this.service.getExperimentInterimResults(payload.eid, selectedLabel).pipe(
        tap((exp: IntermediateExperiment) => {
          if (exp) {
            const interimExperiment = exp;
            if (interimExperiment.multResLabels && interimExperiment.multResLabels.length) {
              interimExperiment.multResLabels.push('score');
            }
            ctx.patchState({
              interimExperiment: {
                ...interimExperiment,
                selectedLabel:
                  selectedLabel ||
                  (interimExperiment.multResLabels && interimExperiment.multResLabels.length
                    ? interimExperiment.multResLabels[interimExperiment.multResLabels.length - 1]
                    : null),
              },
            });
          }
        }),
        catchError((err: HttpErrorResponse) => {
          const notification: AppNotification = {
            type: NOTIFICATION_TYPE.ERROR,
            receivedAt: new Date().getTime(),
            message: this.utilsService.formatErrorMessage(err),
          };
          this.store.dispatch(new AddNotification(notification));
          this.snackbarService.error(this.utilsService.formatErrorMessage(err));
          return throwError(err);
        })
      );
    }
  }

  @Action(SetInterimExperiment)
  setInterimExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: SetInterimExperiment): void {
    if (!payload) {
      return;
    }
    ctx.patchState({
      interimExperiment: payload,
    });
  }

  @Action(CreateExperiment)
  createExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: CreateExperiment): Observable<any> {
    if (!payload) {
      return;
    }
    return this.service.createExperiment(payload).pipe(
      tap((res) => {
        if (res) {
          const message = 'Experiment created!';
          const notification: AppNotification = {
            type: NOTIFICATION_TYPE.SUCCESS,
            receivedAt: new Date().getTime(),
            message,
          };
          this.store.dispatch(new AddNotification(notification));
          this.snackbarService.success(message);
          this.store.dispatch(new Navigate(['/list']));
          return;
        }
      }),
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(DeleteExperiment)
  deleteExperiment(ctx: StateContext<ExperimentStateModel>, { payload }: DeleteExperiment): Observable<any> {
    const state = ctx.getState();
    if (!payload) {
      return;
    }
    return this.service.deleteExperiment(payload).pipe(
      tap(() => {
        const experiments = state.experiments.slice();
        const foundIndex = experiments.findIndex((item) => item.eid === payload);
        if (foundIndex !== -1) {
          experiments.splice(foundIndex, 1);
          const message = 'Experiment deleted!';
          const notification: AppNotification = {
            type: NOTIFICATION_TYPE.SUCCESS,
            receivedAt: new Date().getTime(),
            message,
          };
          this.store.dispatch(new AddNotification(notification));
          this.snackbarService.success(message);
          ctx.patchState({
            experiments,
          });
        }
      }),
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }

  @Action(RefreshAll)
  refreshAll(ctx: StateContext<ExperimentStateModel>): Observable<any> {
    return this.service.refreshAll().pipe(
      catchError((err: HttpErrorResponse) => {
        const notification: AppNotification = {
          type: NOTIFICATION_TYPE.ERROR,
          receivedAt: new Date().getTime(),
          message: this.utilsService.formatErrorMessage(err),
        };
        this.store.dispatch(new AddNotification(notification));
        this.snackbarService.error(this.utilsService.formatErrorMessage(err));
        return throwError(err);
      })
    );
  }
}
