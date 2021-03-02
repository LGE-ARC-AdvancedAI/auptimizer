/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { DomSanitizer } from '@angular/platform-browser';

import { environment } from '../../../environments/environment';

const apiUrl = environment.apiUrl;

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  constructor(private http: HttpClient, private sanitizer: DomSanitizer) {}

  public get<T>(endpoint: string, params?: HttpParams | { [key: string]: any }): Observable<T> {
    console.warn('Network: GET', `${apiUrl}/${endpoint}`, params ? params : {});
    return this.http.get<T>(`${apiUrl}/${endpoint}`, { params });
  }
  public post<T>(endpoint: string, object?, params?: HttpParams | { [key: string]: any }): Observable<T> {
    return this.http.post<T>(`${apiUrl}/${endpoint}`, object, { params });
  }
  public put<T>(endpoint: string, object): Observable<T> {
    return this.http.put<T>(`${apiUrl}/${endpoint}`, object);
  }
  public delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${apiUrl}/${endpoint}`);
  }
  public patch<T>(endpoint: string, object): Observable<T> {
    return this.http.patch<T>(`${apiUrl}/${endpoint}`, object);
  }
}
