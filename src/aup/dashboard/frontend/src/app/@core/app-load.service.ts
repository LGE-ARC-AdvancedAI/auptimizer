import { Injectable } from '@angular/core';
import { Store } from '@ngxs/store';
import { SetTheme, GetDatabaseLink } from '../appStore/app.actions';
import { ColorSchemeService } from '../shared/services/color-scheme.service';
import { CUSTOM_ICONS } from '../models/data/custom-icons.data';
import { MatIconRegistry } from '@angular/material/icon';
import { DomSanitizer } from '@angular/platform-browser';

@Injectable()
export class AppLoadService {
  constructor(
    private store: Store,
    public colorSchemeService: ColorSchemeService,
    readonly matIconRegistry: MatIconRegistry,
    readonly domSanitizer: DomSanitizer
  ) {
    CUSTOM_ICONS.map((icon) => {
      this.matIconRegistry.addSvgIcon(icon.name, this.domSanitizer.bypassSecurityTrustResourceUrl(icon.path));
    });
  }

  initializeApplication(): void {
    this.store.dispatch(new GetDatabaseLink());
    this.setTheme();
  }

  setTheme(): void {
    this.colorSchemeService.load();
    this.store.dispatch(new SetTheme());
  }
}
