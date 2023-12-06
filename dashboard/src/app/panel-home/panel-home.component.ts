import {Component, Inject, Injector} from '@angular/core'
import {FormControl, Validators} from "@angular/forms"
import {EnvironmentService} from "../services/enviroment.service"
import {SubEnvironmentInterface} from "../../environments/environment-interface"
import {TuiAlertService, TuiDialogService} from "@taiga-ui/core"
import {PolymorpheusComponent} from '@tinkoff/ng-polymorpheus'
import {JsonViewerComponent} from "../json-viewer/json-viewer.component"
import {ApolloManagerService} from "../services/apollo-manager-service"
import {LoadingService} from "../services/Loading.service"
import {switchMap} from "rxjs"
import {QuoteService} from "./quote.service"

@Component({
    selector: 'app-panel-home',
    templateUrl: './panel-home.component.html',
    styleUrl: './panel-home.component.scss',
})
export class PanelHomeComponent {
    quoteForm = new FormControl<number | null>(null, Validators.required)
    environmentForm = new FormControl<SubEnvironmentInterface | null>(null)
    environments: SubEnvironmentInterface[]
    assetsFolder: string


    constructor(readonly environmentService: EnvironmentService,
                readonly loadingService: LoadingService,
                readonly quoteService: QuoteService,
                @Inject(TuiAlertService) protected readonly alert: TuiAlertService,
                @Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
                @Inject(Injector) private readonly injector: Injector) {
        this.environments = environmentService.getValue("environments")
        this.assetsFolder = environmentService.getValue("assetsFolder")
        this.environmentForm.setValue(this.environments[this.environments.length - 1])
    }

    selectedEnvironment(): SubEnvironmentInterface | null {
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
