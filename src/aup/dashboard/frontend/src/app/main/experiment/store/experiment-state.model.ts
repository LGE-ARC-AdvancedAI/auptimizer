/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { EXPERIMENT_VIEW_TYPE } from '../../../models/enum/experiment-view-type.enum';
import { Experiment } from '../../../models/experiment.model';
import { NavItem } from '../../../models/nav-items.model';
import { Resource } from '../../../models/resource.model';

export interface ExperimentStateModel {
  experiments: Experiment[];
  experimentsMultiplier: number;
  resources: Resource[];
  selectedExperiment: SelectedExperiment;
  hyperparameters: Hyperparameters;
  jobStatusSortCriteria: JobStatusSortCriteria;
  jobs: JobStatus[];
  jobsGraphData?: PlotlyScatterGraph;
  jobsMultipleResults: {
    labels: string[];
    selectedLabel: string;
  };
  firstValidJobNumber: number;
  jobsOptimizationGraphData?: PlotlyScatterGraph;
  jobsMultiplier: number;
  metricsVsHparams: any;
  parallelCoordinatesTrace: ParallelCoordinates;
  refreshIntervalOptions: number[];
  refreshInterval: number;
  refreshingInterval: boolean;
  sidenavOpen: boolean;
  experimentViewType: EXPERIMENT_VIEW_TYPE;
  intermResults: IntermediateExperiment[];
  interimExperiment: IntermediateExperiment;
  navItems: NavItem[];
  loadingExperiment: boolean;
  loadingAllExperiments: boolean;
  loadingIntermResults: boolean;
}

export interface SelectedExperiment {
  bestScore: BestScore;
  experiment: Experiment;
  jobStats: {
    finished: number;
    unfinished: number;
    total: number;
  };
}

export interface BestScore {
  proposer?: string;
  score: number;
  params?: BestScoreParam[];
  configList?: any;
}

export interface BestScoreParam {
  name: string;
  range: any;
  type: string;
  value: number;
  interval: number;
  n: number;
}

export interface Hyperparameters {
  numSamples: number;
  parameters: any;
  proposer: string;
}

export interface JobStatusSortCriteria {
  sortby: string;
  asc: 0 | 1;
}

export interface JobStatus {
  eid: number;
  endTime: number;
  jid: number;
  jobConfig: any;
  rid: number;
  score: any;
  startTime: number;
  status: string;
  tableData?: any;
  tableFullData?: any;
  tableHyperParams?: any;
}

export interface PlotlyScatterGraph {
  x: number[];
  y: number[];
  type: string;
  mode: string;
}

export interface ExperimentHistory {
  jid: number;
  jobConfig: any;
  score: any;
}

export interface StartExperimentModel {
  eid: number;
}

export interface SetupDB {
  work_dir: string;
  ini_path: string;
  overwrite: boolean;
  cpu?: number;
  aws_file?: string;
  gpu_file?: string;
  node_file?: string;
}

export interface CreateExperimentModel {
  json_config_body: any;
  cwd: string;
}

export interface ParallelCoordinates {
  dimensions: { label: string; values: [] }[];
  line: any;
  type: string;
}

export interface IntermediateExperiment {
  eid: number;
  name: string;
  scriptName: string;
  jobs?: IntermediateJob[];
  multResLabels?: string[];
  selectedLabel?: string;
}

export interface IntermediateJob {
  jid: number;
  interimResults: IntermediateResult[];
}

export interface IntermediateResult {
  irid: number;
  receiveTime: number;
  score: number;
}
