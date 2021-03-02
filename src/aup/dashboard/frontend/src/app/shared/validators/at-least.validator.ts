/* eslint-disable prefer-arrow/prefer-arrow-functions */
import { FormGroup, ValidatorFn } from '@angular/forms';

// eslint-disable-next-line @typescript-eslint/naming-convention
export function AtLeastValidator(minimumValues: number): ValidatorFn {
  return (formGroup: FormGroup): { [key: string]: boolean } | null => {
    let numberValues = 0;
    Object.keys(formGroup.controls).forEach((key) => {
      const control = formGroup.controls[key];
      if (control.value) {
        numberValues++;
      }
    });

    if (numberValues < minimumValues) {
      return { minimumValues: true };
    }
    return null;
  };
}
