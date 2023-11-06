import {Component, Inject} from "@angular/core"
import {Router} from "@angular/router"
import {EnvironmentService} from "./services/enviroment.service"
import {Observable} from "rxjs"
import {TuiNightThemeService} from "@taiga-ui/core"

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
		@Inject(TuiNightThemeService) readonly night$: Observable<boolean>
	) {
		this.assetsFolder = environmentService.getValue("assetsFolder")
		this.mainColor = environmentService.getValue("mainColor")
		this.aggregated = environmentService.getValue("aggregate")
		let favIcon: HTMLLinkElement = document.querySelector('#favIcon')!
		favIcon.href = `assets/${this.assetsFolder}/favicon.ico`
	}

	ngOnInit() {
		this.router.navigate(["/home"])
	}
}
