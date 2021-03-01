/* eslint-disable @typescript-eslint/no-floating-promises */
import { SecToMinPipe } from './sec-to-min.pipe';

describe('SecToMinPipe', () => {
  it('create an instance', () => {
    const pipe = new SecToMinPipe();
    expect(pipe).toBeTruthy();
  });
});
