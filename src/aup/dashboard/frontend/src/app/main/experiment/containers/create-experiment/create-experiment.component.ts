/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/unbound-method */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { Component, OnInit, OnDestroy, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import * as JSONEditor from 'jsoneditor';
import * as exampleJSON from './exampleJSON';
import { Store, Select } from '@ngxs/store';
import { CreateExperiment, GetExperiment } from '../../store/experiment.actions';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CreateExperimentModel, SelectedExperiment } from '../../store/experiment-state.model';
import { ActivatedRoute, Router } from '@angular/router';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription } from 'rxjs';
import { HelperService, SnackbarService } from '../../../../shared/services';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ConfirmDialogComponent } from '../../../../shared/dialogs/confirm/confirm-dialog.component';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-create-experiment',
  templateUrl: './create-experiment.component.html',
  styleUrls: ['./create-experiment.component.scss'],
})
export class CreateExperimentComponent implements OnInit, OnDestroy {
  options: any;
  jsonEditorCode: any;
  jsonEditorTree: any;
  jsonCode: any;
  experimentConfig;
  createExperimentForm: FormGroup;
  @Select(ExperimentState.selectedExperiment) selectedExperiment$: Observable<SelectedExperiment>;

  experimentId: number;
  subscriptions: Subscription;

  showInteractionGuide = false;
  jsonHasError = false;
  autoConvert = true;
  errMessage: string = null;
  confirmDialogRef: MatDialogRef<ConfirmDialogComponent>;

  constructor(
    readonly store: Store,
    public dialog: MatDialog,
    private fb: FormBuilder,
    readonly route: ActivatedRoute,
    readonly router: Router,
    public helperService: HelperService,
    private cdRef: ChangeDetectorRef,
    private snackbarService: SnackbarService
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    const id = this.route.snapshot.params.id;
    this.initForm();
    this.clear();
    if (id) {
      this.experimentId = id;
      this.store.dispatch(new GetExperiment(this.experimentId));
      this.subscriptions.add(
        this.selectedExperiment$.subscribe((selectedExperiment: SelectedExperiment) => {
          if (selectedExperiment && this.experimentId) {
            this.clear();
            const workingDir = selectedExperiment.experiment.expConfig['workingdir'];
            const resource = selectedExperiment.experiment.expConfig['resource'];
            const cwd = selectedExperiment.experiment.expConfig['cwd'];
            this.createExperimentForm.patchValue({
              cwd: cwd || workingDir,
            });
            if (workingDir && resource !== 'node') {
              delete selectedExperiment.experiment.expConfig['workingdir'];
            }
            if (cwd) {
              delete selectedExperiment.experiment.expConfig['cwd'];
            }
            this.experimentConfig = selectedExperiment.experiment.expConfig;
            this.initEditor();
            this.cdRef.markForCheck();
          }
        })
      );
    } else {
      this.experimentConfig = exampleJSON.example;
      this.initEditor();
      this.cdRef.markForCheck();
    }
  }

  initForm(): void {
    this.createExperimentForm = this.fb.group({
      cwd: ['', [Validators.required]],
    });
  }

  initEditor(): void {
    this.options = {
      code: {
        mode: 'code',
        onChange: () => {
          let json;
          try {
            json = this.jsonEditorCode.get();
          } catch (err) {
            this.jsonHasError = true;
            this.errMessage = err;
            this.cdRef.markForCheck();
          }
          if (json) {
            this.jsonHasError = false;
            this.jsonCode = json;
            if (this.autoConvert) {
              this.validateJSON('Tree');
            }
            this.cdRef.markForCheck();
          }
        },
      },
      tree: {
        mode: 'tree',
        onChange: () => {
          let json;
          try {
            json = this.jsonEditorTree.get();
          } catch (err) {
            this.jsonHasError = true;
            this.snackbarService.error(err);
            this.cdRef.markForCheck();
          }
          if (json) {
            this.jsonHasError = false;
            this.jsonCode = json;
            this.validateJSON('Code');
            this.cdRef.markForCheck();
          }
        },
      },
    };
    this.jsonEditorCode = new JSONEditor(document.getElementById('jsonEditorCode'), this.options.code);
    this.jsonEditorTree = new JSONEditor(document.getElementById('jsonEditorTree'), this.options.tree);
    this.jsonCode = this.experimentConfig;
    this.validateJSON('Code');
    if (this.autoConvert) {
      this.validateJSON('Tree');
    }
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.clear();
  }

  clear(): void {
    this.experimentConfig = null;
    this.jsonCode = null;
    this.jsonEditorCode = null;
    this.jsonEditorTree = null;
    this.options = null;
  }

  validateJSON = (type) => {
    if (type === 'Tree') {
      this.jsonEditorTree.set(this.jsonCode);
    } else if (type === 'Code') {
      this.jsonEditorCode.set(this.jsonCode);
    }
  };

  onCancel(): void {
    this.confirmDialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: 'Cancel and go back?',
        content:
          'Are you sure you want to cancel creating this experiment? Everything you added will be lost and you will return to the experiment list page.',
        confirmButtonText: 'Confirm',
      },
      panelClass: 'header-modal',
    });
    this.confirmDialogRef.afterClosed().subscribe((confirm) => {
      if (confirm) {
        this.helperService.redirectTo('/list');
      }
    });
  }

  onCreateExperiment(): void {
    if (!this.createExperimentForm.valid || !this.jsonCode || this.jsonHasError) {
      return;
    }
    if (this.jsonHasError) {
      this.snackbarService.error(this.errMessage);
      return;
    }
    const createExperimentModel: CreateExperimentModel = {
      cwd: this.createExperimentForm.value.cwd,
      json_config_body: this.jsonCode,
    };
    this.store.dispatch(new CreateExperiment(createExperimentModel));
  }
}
