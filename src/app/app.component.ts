import {Component, Inject} from "@angular/core"
import {Router} from "@angular/router"
import {EnvironmentService} from "./services/enviroment.service"
import {Observable} from "rxjs"
import {StateService} from "./services/state.service"
import {FormControl} from "@angular/forms"
import {EnvironmentInterface} from "../environments/environment-interface"
import {takeUntilDestroyed} from "@angular/core/rxjs-interop"

@Component({
    selector: "app-root",
    templateUrl: "./app.component.html",
    styleUrls: ["./app.component.scss"],
    standalone: false
})
export class AppComponent {
	readonly assetsFolder: string
	readonly mainColor: string
	readonly aggregated: boolean
	readonly panel: boolean

	environmentForm = new FormControl<EnvironmentInterface | null>(null)

	constructor(
		private readonly router: Router,
		readonly environmentService: EnvironmentService,
		readonly stateService: StateService
	) {
		this.assetsFolder = environmentService.getValue("assetsFolder")
		this.mainColor = environmentService.getValue("mainColor")
		this.aggregated = environmentService.environments.length > 1
		this.panel = environmentService.getValue("panel")
		let favIcon: HTMLLinkElement = document.querySelector('#favIcon')!
		favIcon.href = `assets/${this.assetsFolder}/favicon.png`
		if (this.panel) {
			this.environmentForm.setValue(this.environmentService.selectedEnvironment.value)
			this.environmentForm.valueChanges
				.pipe(
					takeUntilDestroyed(),
				)
				.subscribe(value => this.environmentService.selectedEnvironment.next(value))
		}
	}

	ngOnInit() {
		this.router.navigate(["/home"])
	}
}
