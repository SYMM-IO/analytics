import {Component, Inject} from '@angular/core'
import {EnvironmentService} from "../services/enviroment.service"
import {TuiAlertService} from "@taiga-ui/core"
import {LoadingService} from "../services/Loading.service"
import {combineLatest} from "rxjs"
import {takeUntilDestroyed} from "@angular/core/rxjs-interop"
import {SnapshotService} from "../services/snapshot.service"
import {HedgerSnapshot} from "../models"

@Component({
	selector: 'app-panel-home',
	templateUrl: './panel-home.component.html',
	styleUrl: './panel-home.component.scss',
})
export class PanelHomeComponent {
	hedgerSnapshotsMaps = new Map<string, HedgerSnapshot>()

	constructor(readonly environmentService: EnvironmentService,
				readonly loadingService: LoadingService,
				readonly snapshotService: SnapshotService,
				@Inject(TuiAlertService) protected readonly alert: TuiAlertService) {
		this.environmentService.selectedEnvironment.pipe(takeUntilDestroyed()).subscribe(env => {
			combineLatest(env!.hedgers!.map(value => snapshotService.loadHedgerSnapshot(env!, value.name!)))
				.subscribe((value: HedgerSnapshot[]) => {
					for (const hedgerSnapshot of value)
						this.hedgerSnapshotsMaps.set(hedgerSnapshot.name!, hedgerSnapshot)
				})
		})
	}
}
