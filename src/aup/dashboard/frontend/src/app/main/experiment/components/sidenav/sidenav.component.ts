/* eslint-disable @typescript-eslint/unbound-method */
import { Component, Input } from '@angular/core';
import { Select, Store } from '@ngxs/store';
import { Observable } from 'rxjs';
import { NavItem } from '../../../../models/nav-items.model';
import { ToggleSideNav } from '../../store/experiment.actions';
import { ExperimentState } from '../../store/experiment.store';

@Component({
  selector: 'app-sidenav',
  templateUrl: './sidenav.component.html',
  styleUrls: ['./sidenav.component.scss'],
})
export class SidenavComponent {
  @Input() sideNavElements: NavItem[];
  @Select(ExperimentState.sidenavOpen) sidenavOpen$: Observable<boolean>;

  listElement: NavItem = {
    displayName: 'Experiments',
    route: '/list',
    iconName: 'west',
    tooltip: 'Experiment list',
  };
  constructor(readonly store: Store) {}

  onToggleSideNav(): void {
    this.store.dispatch(new ToggleSideNav());
  }
}
