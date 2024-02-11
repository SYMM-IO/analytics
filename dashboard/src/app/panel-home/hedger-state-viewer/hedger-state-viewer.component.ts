import {Component, Input} from '@angular/core'
import {Hedger} from "../../../environments/environment-interface"
import {AffiliateSnapshot, HedgerSnapshot} from "../../models"
import {combineLatest} from "rxjs"
import {EnvironmentService} from "../../services/enviroment.service"
import {SnapshotService} from "../../services/snapshot.service"

@Component({
	selector: 'hedger-state-viewer',
	templateUrl: './hedger-state-viewer.component.html',
	styleUrl: './hedger-state-viewer.component.scss',
})
export class HedgerStateViewerComponent {
	affiliateSnapshotsMaps = new Map<string, AffiliateSnapshot>()

	@Input() hedgerSnapshot!: HedgerSnapshot | undefined
	@Input() hedger!: Hedger

	constructor(readonly environmentService: EnvironmentService,
				readonly snapshotService: SnapshotService) {

	}

	onOpen(value: boolean) {
		if (!value)
			return
		let env = this.environmentService.selectedEnvironment.value
		combineLatest(env!.affiliates!.map(value => this.snapshotService.loadAffiliateSnapshot(env!, this.hedger.name!, value.name!)))
			.subscribe((value: AffiliateSnapshot[]) => {
				for (const affiliateSnapshot of value)
					this.affiliateSnapshotsMaps.set(affiliateSnapshot.name!, affiliateSnapshot)
			})
	}

	protected readonly isNaN = isNaN
}
