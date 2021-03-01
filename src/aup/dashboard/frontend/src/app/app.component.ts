import { Component } from '@angular/core';
import { Store } from '@ngxs/store';
import { GetNotifications } from './appStore/app.actions';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
})
export class AppComponent {
  title = 'Auptimizer-Dashboard';

  constructor(private store: Store) {
    this.store.dispatch(new GetNotifications());
  }
}
