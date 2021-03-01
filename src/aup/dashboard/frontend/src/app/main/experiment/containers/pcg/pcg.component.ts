/* eslint-disable @typescript-eslint/naming-convention */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-expressions */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/unbound-method */
import { Component, OnInit, ChangeDetectorRef, ChangeDetectionStrategy, OnDestroy } from '@angular/core';
import { Store, Select } from '@ngxs/store';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription, Observable } from 'rxjs';
import { GetExperiment, GetMetricVsHparams } from '../../store/experiment.actions';
import { ExperimentState } from '../../store/experiment.store';
import { AppState } from '../../../../appStore/app.store';
import { Theme } from '../../../../appStore/app-state.model';
import { ParallelCoordinates, SelectedExperiment } from '../../store/experiment-state.model';
import { MatSelectChange } from '@angular/material/select';
import { PlotlyService } from 'angular-plotly.js';
import { TruncatePipe } from '../../../../shared/pipes/truncate.pipe';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  selector: 'app-pcg',
  templateUrl: './pcg.component.html',
  styleUrls: ['./pcg.component.scss'],
})
export class PcgComponent implements OnInit, OnDestroy {
  subscriptions: Subscription;
  experimentId: number;
  initialTraces: { label: string; values: [] }[];
  selected: { label: string; values: [] }[];
  hyperParamTraces: { label: string; values: [] }[];
  initialAllowedParams = 3;
  selectedExperiment: SelectedExperiment;

  @Select(AppState.theme) theme$: Observable<Theme>;
  @Select(ExperimentState.metricsVsHparams) metricsVsHparams$: Observable<any>;
  @Select(ExperimentState.selectedExperiment) selectedExperiment$: Observable<SelectedExperiment>;
  @Select(ExperimentState.parallelCoordinatesTrace) parallelCoordinatesTrace$: Observable<any>;
  @Select(ExperimentState.sidenavOpen) sidenavOpen$: Observable<boolean>;

  theme: Theme;
  public graph = {
    data: [],
    layout: {
      height: 540,
      title: 'Hyperparameter Interaction Graph',
      showlegend: true,
    },
    config: {
      responsive: true,
      displayModeBar: false,
      scrollZoom: true,
    },
  };

  width = window.innerWidth;
  height = window.innerHeight;

  showInteractionGuide = false;

  constructor(
    readonly store: Store,
    private route: ActivatedRoute,
    private cdRef: ChangeDetectorRef,
    private plotlyService: PlotlyService,
    readonly router: Router
  ) {}

  ngOnInit(): void {
    this.subscriptions = new Subscription();
    this.subscriptions.add(
      this.route?.parent?.params.subscribe((params) => {
        this.experimentId = params['id'];
        if (this.experimentId) {
          this.store.dispatch(new GetExperiment(this.experimentId));
          this.store.dispatch(new GetMetricVsHparams(this.experimentId));
        }
      })
    );
    this.subscriptions.add(
      this.selectedExperiment$.subscribe((experiment: SelectedExperiment) => {
        if (experiment) {
          this.selectedExperiment = experiment;
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.sidenavOpen$.subscribe((sidenavOpen: boolean) => {
        if (sidenavOpen !== null && sidenavOpen !== undefined && this.theme) {
          window.dispatchEvent(new Event('resize'));
          // window.resizeTo(this.width / 2, this.height / 2);
          // window.resizeTo(
          //   window.screen.availWidth / 2,
          //   window.screen.availHeight / 2
          // );
          this.cdRef.detectChanges();
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.parallelCoordinatesTrace$.subscribe((traces: ParallelCoordinates) => {
        if (traces) {
          const truncate = new TruncatePipe();
          this.hyperParamTraces = traces.dimensions.slice();
          this.hyperParamTraces.map((trace) => {
            trace.label = truncate.transform(trace.label, [30, '...']);
          });
          this.initialTraces = [];
          this.selected = [];
          const foundIndex = this.hyperParamTraces.findIndex((item) => item.label.toLowerCase() === 'score');
          if (foundIndex !== -1) {
            this.initialTraces.push(this.hyperParamTraces[foundIndex]);
            this.hyperParamTraces.splice(foundIndex, 1);
            for (let i = 0; i < this.initialAllowedParams; i++) {
              if (this.hyperParamTraces[i]) {
                // this.initialTraces.push(this.hyperParamTraces[i]);
                this.selected.push(this.hyperParamTraces[i]);
              }
            }
            // this.hyperParamTraces.splice(0, this.initialAllowedParams);
          }
          const initialTraces: ParallelCoordinates = {
            line: traces.line,
            type: traces.type,
            dimensions: [...this.selected, ...this.initialTraces],
          };
          this.graph.data = [initialTraces];
          this.cdRef.markForCheck();
        } else {
          this.hyperParamTraces = [];
          this.initialTraces = [];
          this.selected = [];
          this.graph.data = [];
          this.cdRef.markForCheck();
        }
      })
    );
    this.subscriptions.add(
      this.theme$.subscribe((theme: Theme) => {
        if (theme) {
          this.theme = theme;
          theme.name === 'dark'
            ? (this.graph.layout = this.changeDarkModeChart())
            : (this.graph.layout = this.changeLightModeChart());
          this.cdRef.markForCheck();
        }
      })
    );
    // this.plotlyService.getPlotly().Fx.hover('test', ['HEEEELOOO']);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
  }

  downloadGraph(): void {
    const graphDiv = this.plotlyService.getInstanceByDivId('hig');
    this.plotlyService
      .getPlotly()
      .downloadImage(graphDiv, { format: 'png', width: '1000', height: '450', filename: 'hig' });
  }

  selectHyperparams(event: MatSelectChange): void {
    if (!event) {
      return;
    }
    this.selected = event.value;
    this.graph.data[0].dimensions = [...this.selected, ...this.initialTraces];
    this.cdRef.markForCheck();
  }

  cleanData(): void {
    this.graph.data = [];
    this.initialTraces = [];
    this.hyperParamTraces = [];
    this.cdRef.markForCheck();
  }

  async toggleExperiment(id: number): Promise<void> {
    if (!id) {
      return;
    }
    this.experimentId = id;
    this.cleanData();
    this.store.dispatch(new GetExperiment(this.experimentId));
    this.store.dispatch(new GetMetricVsHparams(this.experimentId));
    await this.router.navigate([`experiment/${id}/hig`]);
  }

  changeLightModeChart(): any {
    return {
      height: 540,
      title: 'Hyperparameter Interaction Graph',
      showlegend: true,
      hovermode: 'closest',
    };
  }

  changeDarkModeChart(): any {
    return {
      hovermode: 'closest',
      plot_bgcolor: '#424242',
      paper_bgcolor: '#424242',
      height: 540,
      title: {
        text: 'Hyperparameter Interaction Graph',
        font: {
          color: '#ffffff',
        },
      },
      showlegend: true,
      // legend: {
      //   color: '#ffffff',
      //   font: {
      //     color: '#ffffff',
      //   },
      // },
      // gridcolor: '#ffffff',
      // tickfont: {
      //   color: '#ffffff',
      // },
      // xaxis: {
      //   showgrid: true,
      //   zeroline: true,
      //   showline: true,
      //   mirror: 'ticks',
      //   gridcolor: '#bdbdbd',
      //   gridwidth: 2,
      //   zerolinecolor: '#969696',
      //   zerolinewidth: 4,
      //   linecolor: '#636363',
      //   linewidth: 6,
      // },
      // yaxis: {
      //   showgrid: true,
      //   zeroline: true,
      //   showline: true,
      //   mirror: 'ticks',
      //   gridcolor: '#bdbdbd',
      //   gridwidth: 2,
      //   zerolinecolor: '#969696',
      //   zerolinewidth: 4,
      //   linecolor: '#636363',
      //   linewidth: 6,
      // },
    };
  }
}
