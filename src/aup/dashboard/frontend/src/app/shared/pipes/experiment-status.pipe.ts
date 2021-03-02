import { Pipe, PipeTransform } from '@angular/core';
import { Experiment } from '../../models/experiment.model';

@Pipe({ name: 'experimentStatus' })
export class ExperimentStatusPipe implements PipeTransform {
  transform(experiment: Experiment): string {
    if (experiment.startTime === -1 && experiment.endTime === -1) {
      return 'Stopping...';
    }
    if (experiment.startTime && experiment.endTime && experiment.startTime !== -1 && experiment.endTime !== -1) {
      return 'Finished';
    } else if (experiment.startTime && experiment.startTime !== -1 && !experiment.endTime) {
      return 'Running';
    } else if (!experiment.startTime && !experiment.endTime) {
      return 'Not started';
    }
  }
}
