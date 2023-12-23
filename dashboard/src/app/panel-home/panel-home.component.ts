import {Component, Inject, Injector} from '@angular/core'
import {FormControl, Validators} from "@angular/forms"
import {EnvironmentService} from "../services/enviroment.service"
import {Affiliate, EnvironmentInterface} from "../../environments/environment-interface"
import {TuiAlertService, TuiDialogService} from "@taiga-ui/core"
import {PolymorpheusComponent} from '@tinkoff/ng-polymorpheus'
import {JsonViewerComponent} from "../json-viewer/json-viewer.component"
import {LoadingService} from "../services/Loading.service"
import {switchMap} from "rxjs"
import {QuoteService} from "./quote.service"
import {takeUntilDestroyed} from "@angular/core/rxjs-interop"

@Component({
    selector: 'app-panel-home',
    templateUrl: './panel-home.component.html',
    styleUrl: './panel-home.component.scss',
})
export class PanelHomeComponent {
    quoteForm = new FormControl<number | null>(null, Validators.required)
    environmentForm = new FormControl<EnvironmentInterface | null>(null)
    affiliateForm = new FormControl<Affiliate | null>(null)
    environments: EnvironmentInterface[]


    constructor(readonly environmentService: EnvironmentService,
                readonly loadingService: LoadingService,
                readonly quoteService: QuoteService,
                @Inject(TuiAlertService) protected readonly alert: TuiAlertService,
                @Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
                @Inject(Injector) private readonly injector: Injector) {
        this.environments = environmentService.getValue("environments")
        this.environmentForm.valueChanges.pipe(takeUntilDestroyed()).subscribe(value => {
            const affiliates = this.selectedEnvironment()!.affiliates!
            this.affiliateForm.setValue(affiliates[affiliates.length - 1])
        })
        this.environmentForm.setValue(this.environments[this.environments.length - 1])
    }

    selectedEnvironment(): EnvironmentInterface | null {
        return this.environmentForm.value
    }

    selectedAffiliate(): Affiliate | null {
        return this.affiliateForm.value
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
