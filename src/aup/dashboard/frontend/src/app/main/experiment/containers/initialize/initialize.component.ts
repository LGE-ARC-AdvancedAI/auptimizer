/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/unbound-method */
/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable no-shadow */
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { AppState } from '../../../../appStore/app.store';
import { Observable } from 'rxjs/internal/Observable';
import { Select, Store } from '@ngxs/store';
import { FormGroup, Validators, FormControl } from '@angular/forms';
import { SetupDB } from '../../store/experiment-state.model';
import { SetupDatabase } from '../../store/experiment.actions';
import { AppNotification, Theme } from '../../../../appStore/app-state.model';
import { ChangeTheme } from '../../../../appStore/app.actions';
import { environment } from '../../../../../environments/environment';
import { BehaviorSubject, Subscription } from 'rxjs';
import { HelperService } from '../../../../shared/services';
import { STEPPER_GLOBAL_OPTIONS } from '@angular/cdk/stepper';
import { AtLeastValidator } from '../../../../shared/validators';

export enum STEP {
  INIT,
  WIZARD,
}

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-initialize',
  templateUrl: './initialize.component.html',
  styleUrls: ['./initialize.component.scss'],
  providers: [
    {
      provide: STEPPER_GLOBAL_OPTIONS,
      useValue: { showError: true },
    },
  ],
})
export class InitializeComponent implements OnInit, OnDestroy {
  @Select(AppState.dbUrl) dbUrl$: Observable<string>;
  @Select(AppState.themes) themes$: Observable<Theme[]>;
  @Select(AppState.theme) theme$: Observable<Theme>;
  @Select(AppState.notifications) notifications$: Observable<AppNotification[]>;

  types = ['cpu', 'aws', 'gpu', 'node'];
  type = 'cpu';
  step = STEP;
  currentStep$ = new BehaviorSubject<number>(STEP.INIT);

  public themes;
  currentTheme = {
    name: null,
    icon: null,
  };
  version: string;
  subscriptions: Subscription;
  showInteractionGuide = false;
  notifications: AppNotification[];

  firstFormGroup: FormGroup;
  secondFormGroup: FormGroup;
  thirdFormGroup: FormGroup;
  overwriteFormGroup: FormGroup;

  constructor(public helperService: HelperService, readonly store: Store, private cdRef: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.firstFormGroup = new FormGroup({
      work_dir: new FormControl('', [Validators.required]),
    });
    this.secondFormGroup = new FormGroup({
      ini_path: new FormControl('', [Validators.required]),
    });
    this.thirdFormGroup = new FormGroup(
      {
        cpu: new FormControl('', [Validators.pattern(/^[0-9]*$/)]),
        aws_file: new FormControl(''),
        gpu_file: new FormControl(''),
        node_file: new FormControl(''),
      },
      AtLeastValidator(1)
    );
    this.overwriteFormGroup = new FormGroup({
      overwrite: new FormControl(false, [Validators.required]),
    });
    this.version = environment.version;
    this.subscriptions.add(
      this.themes$.subscribe((themes: Theme[]) => {
        this.themes = themes;
        this.cdRef.markForCheck();
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        this.currentTheme = theme;
        this.cdRef.markForCheck();
      })
    );
    this.subscriptions.add(
      this.dbUrl$.subscribe((dbUrl: string) => {
        if (dbUrl) {
          this.overwriteFormGroup.controls.overwrite.setValidators(Validators.requiredTrue);
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.notifications$.subscribe((notifications: AppNotification[]) => {
        if (notifications) {
          this.notifications = notifications;
          this.cdRef.markForCheck();
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  setTheme(): void {
    if (this.themes && this.themes.length) {
      if (this.currentTheme === this.themes[0]) {
        this.currentTheme = this.themes[1];
      } else {
        this.currentTheme = this.themes[0];
      }
      this.store.dispatch(new ChangeTheme(this.currentTheme));
    }
  }

  createDatabaseStep(): void {
    this.currentStep$.next(STEP.WIZARD);
  }

  databaseInitStep(): void {
    this.currentStep$.next(STEP.INIT);
  }

  setType(value: string): void {
    if (!value) {
      return;
    }
    this.type = value;
    this.thirdFormGroup.reset();
    this.cdRef.markForCheck();
  }

  onSubmit(): void {
    if (
      !this.firstFormGroup.valid ||
      !this.secondFormGroup.valid ||
      !this.thirdFormGroup.valid ||
      !this.overwriteFormGroup.valid
    ) {
      return;
    }
    const setupParams: SetupDB = {
      work_dir: this.firstFormGroup.value.work_dir,
      ini_path: this.secondFormGroup.value.ini_path,
      overwrite: this.overwriteFormGroup.value.overwrite,
    };
    switch (this.type) {
      case 'cpu':
        setupParams.cpu = this.thirdFormGroup.value.cpu;
        break;
      case 'aws':
        setupParams.aws_file = this.thirdFormGroup.value.aws_file;
        break;
      case 'gpu':
        setupParams.gpu_file = this.thirdFormGroup.value.gpu_file;
        break;
      case 'node':
        setupParams.node_file = this.thirdFormGroup.value.node_file;
        break;
    }
    this.store.dispatch(new SetupDatabase(setupParams));
  }
}
