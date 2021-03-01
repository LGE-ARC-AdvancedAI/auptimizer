/* eslint-disable @typescript-eslint/no-floating-promises */
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { SharedModule } from '../../../../shared/shared.module';

import { CreateExperimentComponent } from './create-experiment.component';

describe('CreateExperimentComponent', () => {
  let component: CreateExperimentComponent;
  let fixture: ComponentFixture<CreateExperimentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      imports: [NgxsModule.forRoot(), BrowserAnimationsModule, RouterTestingModule, SharedModule],
      declarations: [CreateExperimentComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CreateExperimentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
