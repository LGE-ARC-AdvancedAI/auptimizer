/* eslint-disable @typescript-eslint/no-floating-promises */
import { FirstLetterUppercasePipe } from './first-letter-uppercase.pipe';

describe('FirstLetterUppercasePipe', () => {
  it('create an instance', () => {
    const pipe = new FirstLetterUppercasePipe();
    expect(pipe).toBeTruthy();
  });
});
