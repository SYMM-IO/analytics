import {Component, Inject, Injector} from '@angular/core'
import {FormControl, Validators} from "@angular/forms"
import {EnvironmentService} from "../services/enviroment.service"
import {EnvironmentInterface} from "../../environments/environment-interface"
import {TuiAlertService, TuiDialogService} from "@taiga-ui/core"
import {PolymorpheusComponent} from '@tinkoff/ng-polymorpheus'
import {JsonViewerComponent} from "../json-viewer/json-viewer.component"
import {LoadingService} from "../services/Loading.service"
import {combineLatest, switchMap} from "rxjs"
import {QuoteService} from "../services/quote.service"
import {takeUntilDestroyed} from "@angular/core/rxjs-interop"
import {SnapshotService} from "../services/snapshot.service"
import {AffiliateSnapshot, HedgerSnapshot} from "../models"

@Component({
    selector: 'app-panel-home',
    templateUrl: './panel-home.component.html',
    styleUrl: './panel-home.component.scss',
})
export class PanelHomeComponent {
    quoteForm = new FormControl<number | null>(null, Validators.required)
    environmentForm = new FormControl<EnvironmentInterface | null>(null)
    environments: EnvironmentInterface[]

    affiliateSnapshotsMaps = new Map<string, AffiliateSnapshot>()
    hedgerSnapshotsMaps = new Map<string, HedgerSnapshot>()

    constructor(readonly environmentService: EnvironmentService,
                readonly loadingService: LoadingService,
                readonly quoteService: QuoteService,
                readonly snapshotService: SnapshotService,
                @Inject(TuiAlertService) protected readonly alert: TuiAlertService,
                @Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
                @Inject(Injector) private readonly injector: Injector) {
        this.environments = environmentService.getValue("environments")
        this.environmentForm.valueChanges.pipe(takeUntilDestroyed()).subscribe(env => {
            combineLatest(env!.hedgers!.map(value => snapshotService.loadHedgerSnapshot(env!, value.name!)))
                .subscribe((value: HedgerSnapshot[]) => {
                    for (const hedgerSnapshot of value)
                        this.hedgerSnapshotsMaps.set(hedgerSnapshot.name!, hedgerSnapshot)
                })

            combineLatest(env!.affiliates!.map(value => snapshotService.loadAffiliateSnapshot(env!, value.name!)))
                .subscribe((value: AffiliateSnapshot[]) => {
                    for (const affiliateSnapshot of value)
                        this.affiliateSnapshotsMaps.set(affiliateSnapshot.name!, affiliateSnapshot)
                })
        })
        this.environmentForm.setValue(this.environments[this.environments.length - 1])
    }

    selectedEnvironment(): EnvironmentInterface | null {
        return this.environmentForm.value
    }

    onLoadQuote() {
        this.quoteService.loadQuote(this.selectedEnvironment()!.subgraphUrl!, this.quoteForm.value!)
            .pipe(
                switchMap(data => this.dialogs.open<number>(
                    new PolymorpheusComponent(JsonViewerComponent, this.injector),
                    {
                        data: data['quote'][0],
                        dismissible: true,
                        label: 'Quote Data',
                    },
                )),
            ).subscribe()
    }
}
