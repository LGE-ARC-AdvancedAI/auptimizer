/* eslint-disable @typescript-eslint/no-explicit-any */
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from '../../../shared/services/api.service';
import { HelperService } from '../../../shared/services/helper.service';
import {
  JobStatusSortCriteria,
  StartExperimentModel,
  SetupDB,
  CreateExperimentModel,
} from '../store/experiment-state.model';

const endpoint = 'experiments';

@Injectable({
  providedIn: 'root',
})
export class ExperimentService {
  constructor(private apiService: ApiService, private helperService: HelperService) {}

  getExperiments<T>(): Observable<T[]> {
    return this.apiService.get<T[]>(`${endpoint}`);
  }

  getExperiment<T>(id: number): Observable<T> {
    if (!id) {
      return;
    }
    return this.apiService.get<T>(`${endpoint}/${id}`);
  }

  getHyperparameters<T>(id: number): Observable<T> {
    if (!id) {
      return;
    }
    return this.apiService.get<T>(`hps_space?eid=${id}`);
  }

  getInterimResults<T>(): Observable<T> {
    return this.apiService.get<T>(`interm_res`);
  }

  getExperimentInterimResults<T>(eid: number, label?: string): Observable<T> {
    if (!eid) {
      return;
    }
    const labelQuery = label && label !== 'score' ? `/${label}` : '';
    return this.apiService.get<T>(`interm_res/${eid}${labelQuery}`);
  }

  getJobsStatus<T>(eid: number, sortCriteria: JobStatusSortCriteria): Observable<T> {
    if (!eid || sortCriteria === null || sortCriteria === undefined) {
      return;
    }
    return this.apiService.get<T>(`job_status?sortby=${sortCriteria.sortby}&asc=${sortCriteria.asc}&eid=${eid}`);
  }

  getMetricsVsHparams<T>(id: number): Observable<T> {
    if (!id) {
      return;
    }
    return this.apiService.get<T>(`metrics_vs_hparams?eid=${id}`);
  }

  getExperimentHistoryBest<T>(id: number, n: number, sortby: string, label?: string): Observable<T> {
    if (!id || !n || !sortby) {
      return;
    }
    const labelQuery = label && label !== 'score' ? `/${label}` : '';
    return this.apiService.get<T>(`experiment_history_best/${id}${labelQuery}?n=${n}&sortby=${sortby}`);
  }

  getAllExperimentHistoryBest<T>(n: number, sortby: string, label?: string): Observable<T> {
    if (!n) {
      return;
    }
    const labelQuery = label && label !== 'score' ? `/${label}` : '';
    const sort = sortby ? `&sortby=${sortby}` : '';
    return this.apiService.get<T>(`experiment_history_best${labelQuery}?n=${n}${sort}`);
  }

  startExperiment<T>(data: StartExperimentModel): Observable<T> {
    if (!data) {
      return;
    }
    return this.apiService.post<T>(`start_experiment`, { ...data });
  }

  stopExperiment<T>(eid: number): Observable<T> {
    if (!eid) {
      return;
    }
    return this.apiService.post<T>(`stop_experiment`, { eid });
  }

  setupDB<T>(params: SetupDB): Observable<T> {
    if (!params) {
      return;
    }
    return this.apiService.post<T>(`setup`, { ...params });
  }

  createExperiment<T>(data: CreateExperimentModel): Observable<T> {
    if (!data) {
      return;
    }
    return this.apiService.post<T>(`create_experiment`, data);
  }

  refreshAll<T>(): Observable<T> {
    return this.apiService.post<T>(`refresh_all`);
  }

  deleteExperiment(eid: number): Observable<any> {
    if (!eid) {
      return;
    }
    return this.apiService.delete(`experiment/${eid}`);
  }
}
