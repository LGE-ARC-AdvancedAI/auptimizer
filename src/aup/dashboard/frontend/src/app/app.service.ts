/* eslint-disable @typescript-eslint/no-explicit-any */
import { Injectable } from '@angular/core';
import { ApiService } from './shared/services/api.service';

@Injectable({ providedIn: 'root' })
export class AppService {
  constructor(private apiService: ApiService) {}

  getDatabaseLink(): any {
    return this.apiService.get<string>(`current_db`);
  }
}
