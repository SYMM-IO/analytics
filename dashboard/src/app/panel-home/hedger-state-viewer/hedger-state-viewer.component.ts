import {Component} from '@angular/core'
import {AffiliateSnapshot, HedgerSnapshot} from "../../models"
import {EnvironmentService} from "../../services/enviroment.service"
import {SnapshotService} from "../../services/snapshot.service"
import {ActivatedRoute} from "@angular/router"
import {takeUntilDestroyed} from "@angular/core/rxjs-interop"
import {Hedger} from "../../../environments/environment-interface"
import {combineLatest, Observable, tap} from "rxjs"
import {map, switchMap} from "rxjs/operators"

@Component({
	selector: 'hedger-state-viewer',
	templateUrl: './hedger-state-viewer.component.html',
	styleUrl: './hedger-state-viewer.component.scss',
})
export class HedgerStateViewerComponent {
	affiliateSnapshotsMaps = new Map<string, AffiliateSnapshot>()

	hedger?: Hedger
	hedgerSnapshot: Observable<HedgerSnapshot>

	constructor(readonly environmentService: EnvironmentService,
				readonly snapshotService: SnapshotService,
				readonly route: ActivatedRoute) {
		this.hedgerSnapshot = route.params
			.pipe(
				takeUntilDestroyed(),
				map(value => {
					let env = this.environmentService.selectedEnvironment.value!
					for (const hedger of env.hedgers!)
						if (hedger.name == value['name'])
							return hedger
					return env.hedgers![0] //Should never happen
				}),
				tap(value => this.hedger = value),
				switchMap(value => {
					let env = this.environmentService.selectedEnvironment.value!
					return snapshotService.loadHedgerSnapshot(env!, value.name!)
				}),
			)
	}

	onOpen(value: boolean) {
		if (!value)
			return
		let env = this.environmentService.selectedEnvironment.value
		combineLatest(env!.affiliates!.map(value => this.snapshotService.loadAffiliateSnapshot(env!, this.hedger!.name!, value.name!)))
			.subscribe((value: AffiliateSnapshot[]) => {
				for (const affiliateSnapshot of value)
					this.affiliateSnapshotsMaps.set(affiliateSnapshot.name!, affiliateSnapshot)
			})
	}

	protected readonly isNaN = isNaN
}
