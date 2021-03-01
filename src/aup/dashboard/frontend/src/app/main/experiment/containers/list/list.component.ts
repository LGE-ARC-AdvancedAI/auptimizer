/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/unbound-method */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/naming-convention */
import {
  Component,
  OnInit,
  ChangeDetectionStrategy,
  ViewChild,
  OnDestroy,
  ChangeDetectorRef,
  TemplateRef,
} from '@angular/core';
import { Store, Select } from '@ngxs/store';
import { Observable, Subscription } from 'rxjs';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort, Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { Experiment } from '../../../../models/experiment.model';
import { Resource } from '../../../../models/resource.model';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { ExperimentState } from '../../store/experiment.store';
import {
  DeleteExperiment,
  GetExperiments,
  SetExperimentDisplayView,
  StartExperiment,
  StopExperiment,
} from '../../store/experiment.actions';
import { FormGroup, FormBuilder, Validators, FormGroupDirective, FormControl } from '@angular/forms';
import { StartExperimentModel } from '../../store/experiment-state.model';
import { HelperService, UtilsService } from '../../../../shared/services';
import { EXPERIMENT_STATUS } from '../../../../models/enum/experiment-status.enum';
import { ConfirmDialogComponent } from '../../../../shared/dialogs/confirm/confirm-dialog.component';
import { MatSelectChange } from '@angular/material/select';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';
import { EXPERIMENT_VIEW_TYPE } from '../../../../models/enum/experiment-view-type.enum';
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-list',
  templateUrl: './list.component.html',
  styleUrls: ['./list.component.scss'],
})
export class ListComponent implements OnInit, OnDestroy {
  @Select(ExperimentState.experiments) experiments$: Observable<Experiment[]>;
  @Select(ExperimentState.resources) resources$: Observable<Resource[]>;
  @Select(ExperimentState.loadingAllExperiments) loadingAllExperiments$: Observable<boolean>;
  @Select(ExperimentState.experimentViewType) experimentViewType$: Observable<EXPERIMENT_VIEW_TYPE>;

  @ViewChild('paginatorExperiment', { static: true }) paginatorExperiment: MatPaginator;
  @ViewChild(MatSort, { static: true }) sortExperiment: MatSort;

  @ViewChild('paginatorResource', { static: true }) paginatorResource: MatPaginator;
  @ViewChild(MatSort, { static: true }) sortResource: MatSort;

  @ViewChild('showConfigDialog', { static: true }) showConfigDialog: TemplateRef<any>;
  @ViewChild('showErrorDialog', { static: true }) showErrorDialog: TemplateRef<any>;
  @ViewChild('startExperimentDialog', { static: true }) startExperimentDialog: TemplateRef<any>;

  showConfigDialogRef;
  showErrorDialogRef;
  readonly EXPERIMENT_COLUMNS = {
    ID: 'ID',
    EXPERIMENT_NAME: 'Experiment Name',
    SCRIPT_NAME: 'Script Name',
    END_TIME: 'End Time',
    STATUS: 'Status',
    CONFIG: 'Config',
    START_TIME: 'Start Time',
    DETAILS: 'Details',
    ACTION: 'Action',
    CREATE: 'Create',
    DELETE: 'Delete',
  };
  displayedExperimentColumns = [
    this.EXPERIMENT_COLUMNS.ID,
    this.EXPERIMENT_COLUMNS.EXPERIMENT_NAME,
    this.EXPERIMENT_COLUMNS.SCRIPT_NAME,
    this.EXPERIMENT_COLUMNS.CONFIG,
    this.EXPERIMENT_COLUMNS.START_TIME,
    this.EXPERIMENT_COLUMNS.END_TIME,
    this.EXPERIMENT_COLUMNS.STATUS,
    this.EXPERIMENT_COLUMNS.DETAILS,
    this.EXPERIMENT_COLUMNS.ACTION,
    this.EXPERIMENT_COLUMNS.CREATE,
    this.EXPERIMENT_COLUMNS.DELETE,
  ];
  readonly RESOURCE_COLUMNS = {
    ID: 'ID',
    NAME: 'Name',
    STATUS: 'Status',
    TYPE: 'Type',
  };
  displayedResourceColumns = [
    this.RESOURCE_COLUMNS.ID,
    this.RESOURCE_COLUMNS.NAME,
    this.RESOURCE_COLUMNS.STATUS,
    this.RESOURCE_COLUMNS.TYPE,
  ];
  dataSourceResource: MatTableDataSource<Resource> = new MatTableDataSource<Resource>();
  confirmDialogRef: MatDialogRef<ConfirmDialogComponent>;
  subscriptions: Subscription;
  pageSize = 8;
  page = 1;

  VIEW_TYPE = EXPERIMENT_VIEW_TYPE;

  sortOptions = [
    this.EXPERIMENT_COLUMNS.ID,
    this.EXPERIMENT_COLUMNS.EXPERIMENT_NAME,
    this.EXPERIMENT_COLUMNS.SCRIPT_NAME,
    this.EXPERIMENT_COLUMNS.START_TIME,
    this.EXPERIMENT_COLUMNS.END_TIME,
    this.EXPERIMENT_COLUMNS.STATUS,
  ];
  sortOption = new FormControl(this.EXPERIMENT_COLUMNS.ID);
  searchStr = new FormControl();
  sortDirectionType: 'asc' | 'desc' = 'desc';
  sortDirections: ('asc' | 'desc')[] = ['asc', 'desc'];

  startExperimentDialogRef;
  startExperimentForm: FormGroup;
  selectedStartExperiment: number;
  EXPERIMENT_STATUS = EXPERIMENT_STATUS;
  showResources = false;
  experiments: Experiment[];
  allExperiments: Experiment[];
  resources: Resource[];
  sort: Sort;

  constructor(
    readonly store: Store,
    private cdRef: ChangeDetectorRef,
    public dialog: MatDialog,
    private fb: FormBuilder,
    private utilsService: UtilsService,
    public helperService: HelperService
  ) {}

  ngOnInit(): void {
    this.store.dispatch(new GetExperiments());
    this.subscriptions = new Subscription();
    this.startExperimentForm = this.fb.group({
      cwd: ['', [Validators.required]],
    });
    this.subscriptions.add(
      this.experiments$.subscribe((experiments: Experiment[]) => {
        if (!this.searchStr.value) {
          this.experiments =
            experiments && experiments.length
              ? experiments.slice().sort((a, b) => this.utilsService.compare(a.eid, b.eid, false))
              : null;
        }
        this.allExperiments =
          experiments && experiments.length
            ? experiments.slice().sort((a, b) => this.utilsService.compare(a.eid, b.eid, false))
            : null;
        if (this.sort) {
          this.sortExperimentData();
        }
        this.cdRef.markForCheck();
      })
    );
    this.subscriptions.add(
      this.resources$.subscribe((resources: Resource[]) => {
        this.dataSourceResource.data = resources && resources.length ? resources.slice() : null;
        this.resources = resources && resources.length ? resources.slice() : null;
        this.dataSourceResource.paginator = this.paginatorResource;
        this.dataSourceResource.sort = this.sortResource;
        this.cdRef.markForCheck();
      })
    );
    this.subscriptions.add(
      this.searchStr.valueChanges.pipe(debounceTime(300), distinctUntilChanged()).subscribe((searchValue) => {
        const searchable = this.utilsService.trimString(searchValue);
        this.searchStringInExperiments(searchable);
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  clearSearch(): void {
    this.searchStr.setValue('');
  }

  changeDisplayView(display: EXPERIMENT_VIEW_TYPE): void {
    if (!display) {
      return;
    }
    this.store.dispatch(new SetExperimentDisplayView(display));
  }

  showConfig(experiment: Experiment): void {
    if (!experiment) {
      // show notification that no config is available
      return;
    }
    const config = JSON.parse(experiment.expConfig);
    this.showConfigDialogRef = this.dialog.open(this.showConfigDialog, {
      width: '650px',
      data: { name: experiment.experimentName, config },
      panelClass: 'info-modal',
    });
    this.subscriptions.add(this.showConfigDialogRef.afterClosed().subscribe());
  }

  showErrorDetails(experiment: Experiment): void {
    if (!experiment || !experiment.errorMsg) {
      // show notification that no config is available
      return;
    }
    this.showErrorDialogRef = this.dialog.open(this.showErrorDialog, {
      width: '650px',
      data: { name: experiment.experimentName, message: experiment.errorMsg },
      panelClass: 'info-modal',
    });
    this.subscriptions.add(this.showErrorDialogRef.afterClosed().subscribe());
  }

  startExperiment(experiment: Experiment): void {
    if (!experiment || !experiment.expConfigDetails.workingdir) {
      return;
    }
    const startExperimentData: StartExperimentModel = {
      eid: experiment.eid,
    };
    this.store.dispatch(new StartExperiment(startExperimentData));
    // this.selectedStartExperiment = eid;
    // this.startExperimentDialogRef = this.dialog.open(this.startExperimentDialog, {
    //   width: '400px',
    //   disableClose: true,
    // });
    // this.subscriptions.add(this.startExperimentDialogRef.afterClosed().subscribe());
  }

  onConfirmStartExperiment(formDirective?: FormGroupDirective): void {
    if (!this.startExperimentForm.valid) {
      return;
    }
    const startExperimentData: StartExperimentModel = {
      eid: this.selectedStartExperiment,
    };
    this.store.dispatch(new StartExperiment(startExperimentData));
    formDirective.resetForm();
    this.startExperimentForm.reset();
  }

  stopExperiment(eid: number): void {
    if (!eid) {
      return;
    }
    this.store.dispatch(new StopExperiment(eid));
  }

  onExpCancel(): void {
    this.startExperimentForm.reset();
  }

  onDetails(eid: number): void {
    if (!eid) {
      return;
    }
    this.helperService.redirectTo('/experiment', eid);
  }

  onSortOption(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    this.sort = {
      active: event.value,
      direction: this.sortDirectionType,
    };
    this.sortExperimentData();
  }

  onSortDirection(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    this.sortDirectionType = event.value;
    this.sort = {
      active: this.sortOption.value,
      direction: event.value,
    };
    this.sortExperimentData();
  }

  sortExperimentData(): boolean {
    const sort = this.sort;
    const data = this.allExperiments.slice();
    if (!sort.active || sort.direction === '') {
      this.experiments = data;
      return;
    }

    this.experiments = data.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      switch (sort.active) {
        case this.EXPERIMENT_COLUMNS.ID:
          return this.utilsService.compare(a.eid, b.eid, isAsc);
        case this.EXPERIMENT_COLUMNS.EXPERIMENT_NAME:
          return this.utilsService.compare(a.experimentName, b.experimentName, isAsc);
        case this.EXPERIMENT_COLUMNS.SCRIPT_NAME:
          return this.utilsService.compare(a.scriptName, b.scriptName, isAsc);
        case this.EXPERIMENT_COLUMNS.START_TIME:
          return this.utilsService.compare(a.startTime, b.startTime, isAsc);
        case this.EXPERIMENT_COLUMNS.END_TIME:
          return this.utilsService.compare(a.endTime, b.endTime, isAsc);
        case this.EXPERIMENT_COLUMNS.STATUS:
          return this.utilsService.compare(a.status, b.status, isAsc);
        default:
          return 0;
      }
    });
  }

  sortResourceData(sort: Sort): boolean {
    const data = this.resources.slice();
    if (!sort.active || sort.direction === '') {
      this.dataSourceResource.data = data;
      return;
    }

    this.dataSourceResource.data = data.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      switch (sort.active) {
        case this.RESOURCE_COLUMNS.ID:
          return this.utilsService.compare(a.rid, b.rid, isAsc);
        case this.RESOURCE_COLUMNS.NAME:
          return this.utilsService.compare(a.name, b.name, isAsc);
        case this.RESOURCE_COLUMNS.STATUS:
          return this.utilsService.compare(a.status, b.status, isAsc);
        case this.RESOURCE_COLUMNS.TYPE:
          return this.utilsService.compare(a.type, b.type, isAsc);
        default:
          return 0;
      }
    });
  }

  searchStringInExperiments(query: string): void {
    this.experiments = this.allExperiments.filter(
      (experiment: Experiment) => this.utilsService.trimString(experiment.experimentName).indexOf(query) >= 0
    );
    this.cdRef.markForCheck();
  }

  deleteExperiment(eid: number): void {
    if (!eid) {
      return;
    }
    this.confirmDialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '450px',
      data: {
        title: 'Delete experiment',
        content: 'Are you sure you want to permanently delete this experiment?',
        confirmButtonText: 'Delete',
      },
      panelClass: 'header-modal',
    });
    this.confirmDialogRef.afterClosed().subscribe((confirm) => {
      if (confirm) {
        this.store.dispatch(new DeleteExperiment(eid));
      }
    });
  }
}
