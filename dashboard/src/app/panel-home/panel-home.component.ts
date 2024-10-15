import { Component, Inject } from "@angular/core"
import { EnvironmentService } from "../services/enviroment.service"
import { TuiAlertService } from "@taiga-ui/core"
import { LoadingService } from "../services/Loading.service"
import { takeUntilDestroyed } from "@angular/core/rxjs-interop"
import { Router } from "@angular/router"

@Component({
	selector: "app-panel-home",
	templateUrl: "./panel-home.component.html",
	styleUrl: "./panel-home.component.scss",
})
export class PanelHomeComponent {
	groups = [
		{
			label: "Hedger Stats",
			items: [],
		},
		{
			label: "Tools",
			items: [
				{
					label: "Quote Loader",
					routerLink: "/home/tools/quote_loader",
				},
			],
		},
	]

	constructor(
		readonly environmentService: EnvironmentService,
		readonly loadingService: LoadingService,
		readonly router: Router,
		@Inject(TuiAlertService) protected readonly alert: TuiAlertService,
	) {
		this.environmentService.selectedEnvironment.pipe(takeUntilDestroyed()).subscribe(env => {
			router.navigate(["home"])
			this.groups[0]["items"].splice(0, this.groups[0]["items"].length)
			this.groups[0]["items"].push(
				...env!.solvers!.map(value => {
					return {
						label: value.name!,
						routerLink: `/home/hedger_stat/${value.name}`,
					}
				}),
			)
		})
	}
}
