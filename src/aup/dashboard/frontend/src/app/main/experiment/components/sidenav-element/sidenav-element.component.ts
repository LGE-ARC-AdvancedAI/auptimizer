/* eslint-disable @typescript-eslint/unbound-method */
import { Component, Input } from '@angular/core';
import { NavItem } from '../../../../models/nav-items.model';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { Select } from '@ngxs/store';
import { Observable } from 'rxjs';
import { ExperimentState } from '../../store/experiment.store';

@Component({
  selector: 'app-sidenav-element',
  templateUrl: './sidenav-element.component.html',
  styleUrls: ['./sidenav-element.component.scss'],
  animations: [
    trigger('indicatorRotate', [
      state('collapsed', style({ transform: 'rotate(0deg)' })),
      state('expanded', style({ transform: 'rotate(180deg)' })),
      transition('expanded <=> collapsed', animate('225ms cubic-bezier(0.4,0.0,0.2,1)')),
    ]),
  ],
})
export class SidenavElementComponent {
  @Select(ExperimentState.sidenavOpen) sidenavOpen$: Observable<boolean>;

  @Input() navItem: NavItem;
  @Input() depth = 0;

  expanded = false;

  onItemSelected(item: NavItem): void {
    if (item.children && item.children.length) {
      this.expanded = !this.expanded;
    }
  }
}
