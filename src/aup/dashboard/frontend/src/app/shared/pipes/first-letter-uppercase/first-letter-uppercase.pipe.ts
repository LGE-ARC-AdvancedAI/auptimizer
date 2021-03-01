import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'flu',
})
export class FirstLetterUppercasePipe implements PipeTransform {
  transform(text: string): string {
    if (text.length === 0) {
      return '';
    }
    return text.charAt(0).toUpperCase() + text.slice(1);
  }
}
