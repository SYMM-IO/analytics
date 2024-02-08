import {Component, Input} from '@angular/core'
import {Affiliate} from "../../../environments/environment-interface"
import {AffiliateSnapshot} from "../../models"

@Component({
	selector: 'affiliate-state-viewer',
	templateUrl: './affiliate-state-viewer.component.html',
	styleUrl: './affiliate-state-viewer.component.scss',
})
export class AffiliateStateViewerComponent {
	@Input() affiliateSnapshot: AffiliateSnapshot | undefined
	@Input() affiliate!: Affiliate
	@Input() decimals: number | undefined
	protected readonly JSON = JSON

	getStatusQuotes() {
		return JSON.parse(this.affiliateSnapshot!.status_quotes!.replaceAll("'", "\""))
	}
}
