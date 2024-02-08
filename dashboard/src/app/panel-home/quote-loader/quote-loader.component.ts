import {Component, Inject, Injector, Input} from '@angular/core'
import {switchMap} from "rxjs"
import {PolymorpheusComponent} from "@tinkoff/ng-polymorpheus"
import {LoadingService} from "../../services/Loading.service"
import {FormControl, Validators} from "@angular/forms"
import {EnvironmentService} from "../../services/enviroment.service"
import {QuoteService} from "../../services/quote.service"
import {TuiAlertService, TuiDialogService} from "@taiga-ui/core"
import {EnvironmentInterface} from "../../../environments/environment-interface"
import {QuoteViewerComponent} from "./quote-viewer/quote-viewer.component"

@Component({
	selector: 'quote-loader',
	standalone: false,
	templateUrl: './quote-loader.component.html',
	styleUrl: './quote-loader.component.scss',
})
export class QuoteLoaderComponent {
	@Input() environment!: EnvironmentInterface | null
	quoteForm = new FormControl<number | null>(null, Validators.required)

	constructor(readonly environmentService: EnvironmentService,
				readonly loadingService: LoadingService,
				readonly quoteService: QuoteService,
				@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
				@Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
				@Inject(Injector) private readonly injector: Injector) {
	}

	onLoadQuote() {
		this.quoteService.loadQuote(this.environment!.subgraphUrl!, this.quoteForm.value!)
			.pipe(
				switchMap(data => this.dialogs.open<number>(
					new PolymorpheusComponent(QuoteViewerComponent, this.injector),
					{
						data: [data['quote'][0], this.environment],
						dismissible: true,
					},
				)),
			).subscribe()
	}
}
