/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, ChangeDetectionStrategy, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { ExperimentState } from '../../store/experiment.store';
import { Observable, Subscription } from 'rxjs';
import { Experiment } from '../../../../models/experiment.model';
import { MatSelectChange } from '@angular/material/select';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-experiment-dropdown',
  templateUrl: './experiment-dropdown.component.html',
  styleUrls: ['./experiment-dropdown.component.scss'],
})
export class ExperimentDropdownComponent implements OnInit, OnDestroy {
  @Select(ExperimentState.experiments) experiments$: Observable<Experiment[]>;

  @Input() experimentId: number;
  @Output() toggleExperiment = new EventEmitter<number>();
  experimentIndex: number;
  subscription: Subscription;

  constructor(readonly store: Store) {}

  ngOnInit(): void {
    this.subscription = new Subscription();
    this.subscription.add(
      this.experiments$.subscribe((experiments: Experiment[]) => {
        if (experiments && experiments.length > 0 && this.experimentId) {
          const foundIndex = experiments.findIndex((item) => {
            return +item.eid === +this.experimentId;
          });
          if (foundIndex !== -1) {
            this.experimentIndex = foundIndex;
          }
        }
      })
    );
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  selectedNewExperiment(event: MatSelectChange): void {
    if (!event.value) {
      return;
    }
    this.toggleExperiment.emit(event.value);
  }
}
