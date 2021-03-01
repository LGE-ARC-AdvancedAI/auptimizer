/* eslint-disable @typescript-eslint/no-floating-promises */
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { NgxsModule } from '@ngxs/store';
import { SharedModule } from '../../../../shared/shared.module';

import { IntermResultsComponent } from './interm-results.component';

describe('IntermResultsComponent', () => {
  let component: IntermResultsComponent;
  let fixture: ComponentFixture<IntermResultsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      schemas: [NO_ERRORS_SCHEMA],
      imports: [NgxsModule.forRoot(), RouterTestingModule, SharedModule],
      declarations: [IntermResultsComponent],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(IntermResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
