import { EXPERIMENT_VIEW_TYPE } from '../../../models/enum/experiment-view-type.enum';
import {
  JobStatusSortCriteria,
  StartExperimentModel,
  SetupDB,
  CreateExperimentModel,
  IntermediateExperiment,
} from './experiment-state.model';

export class GetExperiments {
  static readonly type = '[Experiment] Getting list of experiments';
}

export class GetExperiment {
  static readonly type = '[Experiment] Get experiment by id';
  constructor(public payload: number) {}
}

export class GetHyperparameters {
  static readonly type = '[Experiment] Get hyperparameters by experiment id';
  constructor(public payload: number) {}
}

export class GetJobStatus {
  static readonly type = '[Experiment] Get job status by experiment id';
  constructor(
    public payload: {
      eid: number;
      sortCriteria?: JobStatusSortCriteria;
    }
  ) {}
}

export class GetExperimentHistory {
  static readonly type = '[Experiment] Get experiment history best by experiment id';
  constructor(
    public payload: {
      eid: number;
      n?: number;
      sortby?: string;
    }
  ) {}
}

// export class GetExperimentsHistoryBest {
//   static readonly type = '[Experiment] Get experiments history best';
//   constructor(public payload?: number) { }
// }

export class GetMetricVsHparams {
  static readonly type = '[Experiment] Get metrics vs hyperparameters by experiment id';
  constructor(public payload: number) {}
}

export class GetInterimResults {
  static readonly type = '[Experiment] Get intermediate results';
}

export class SetInterimExperiment {
  static readonly type = '[Experiment] Set intermediate experiment';
  constructor(public payload: IntermediateExperiment) {}
}

export class GetExperimentInterimResults {
  static readonly type = '[Experiment] Get experiment intermediate results';
  constructor(public payload: { eid: number; label?: string }) {}
}

export class SetRefreshInterval {
  static readonly type = '[Config] Set refresh interval value';
  constructor(public payload: number) {}
}

export class RefreshInterval {
  static readonly type = '[Config] Refresh interval';
  constructor(public payload: boolean) {}
}

export class StartExperiment {
  static readonly type = '[Experiment] Start experiment by id';
  constructor(public payload: StartExperimentModel) {}
}

export class StopExperiment {
  static readonly type = '[Experiment] Stop experiment by id';
  constructor(public payload: number) {}
}

export class SetupDatabase {
  static readonly type = '[Database] Initialize setup database';
  constructor(public payload: SetupDB) {}
}

export class CreateExperiment {
  static readonly type = '[Experiment] Create experiment';
  constructor(public payload: CreateExperimentModel) {}
}

export class ToggleSideNav {
  static readonly type = '[Sidenav] Toggle sidenav';
}

export class RefreshAll {
  static readonly type = '[Experiment] Refresh all';
}

export class DeleteExperiment {
  static readonly type = '[Experiment] Delete experiment';
  constructor(public payload: number) {}
}

export class SetExperimentDisplayView {
  static readonly type = '[Experiment] Set experiment display view';
  constructor(public payload: EXPERIMENT_VIEW_TYPE) {}
}

export class ChangeJobsGraphForLabel {
  static readonly type = '[Experiment] Change job status graph for multiple labels';
  constructor(public payload: string) {}
}
