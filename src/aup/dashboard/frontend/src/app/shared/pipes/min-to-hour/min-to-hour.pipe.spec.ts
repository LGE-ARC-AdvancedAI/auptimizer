/* eslint-disable @typescript-eslint/no-floating-promises */
import { MinToHourPipe } from './min-to-hour.pipe';

describe('MinToHourPipe', () => {
  it('create an instance', () => {
    const pipe = new MinToHourPipe();
    expect(pipe).toBeTruthy();
  });
});
