import {Component, Inject} from "@angular/core"
import {Router} from "@angular/router"
import {EnvironmentService} from "./services/enviroment.service"
import {Observable} from "rxjs"
import {TuiNightThemeService} from "@taiga-ui/core"
import {StateService} from "./state.service"

@Component({
	selector: "app-root",
	templateUrl: "./app.component.html",
	styleUrls: ["./app.component.scss"],
})
export class AppComponent {
	readonly assetsFolder: string
	readonly mainColor: string
	readonly aggregated: boolean

	constructor(
		private readonly router: Router,
		readonly environmentService: EnvironmentService,
		readonly stateService: StateService,
		@Inject(TuiNightThemeService) readonly night$: Observable<boolean>,
	) {
		this.assetsFolder = environmentService.getValue("assetsFolder")
		this.mainColor = environmentService.getValue("mainColor")
		this.aggregated = environmentService.getValue("aggregate")
		let favIcon: HTMLLinkElement = document.querySelector('#favIcon')!
		favIcon.href = `assets/${this.assetsFolder}/favicon.ico`
		night$.subscribe(value => stateService.nightMode.next(true))// should be value instead of true later
	}

	ngOnInit() {
		this.router.navigate(["/home"])
	}
}
