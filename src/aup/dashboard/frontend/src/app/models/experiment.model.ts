/* eslint-disable @typescript-eslint/no-explicit-any */
export interface Experiment {
  bestScore: number;
  scores: number[];
  eid: number;
  endTime: number;
  expConfig: any;
  scriptName: string;
  status: string;
  experimentName: string;
  startTime: number;
  uid: number;
  jobsFinished: number;
  jobsUnfinished: number;
  jobs?: any;
  history?: ExperimentHistory[];
  expConfigDetails: any;
  errorMsg: string;
  labels: string[];
}

export interface ExperimentHistory {
  jid: number;
  jobConfig: any;
  score: any;
}
