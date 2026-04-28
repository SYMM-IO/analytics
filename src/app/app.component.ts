import {Component, HostListener, Inject} from "@angular/core"
import {Router} from "@angular/router"
import {EnvironmentService} from "./services/enviroment.service"
import {Observable} from "rxjs"
import {StateService} from "./services/state.service"
import {FilterToolbarService} from "./services/filter-toolbar.service"
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
		readonly stateService: StateService,
		readonly filterToolbar: FilterToolbarService,
	) {
		this.assetsFolder = environmentService.getValue("assetsFolder")
		this.mainColor = environmentService.getValue("mainColor")
		this.aggregated = environmentService.environments.length > 1
		this.panel = environmentService.getValue("panel")
		let favIcon: HTMLLinkElement = document.querySelector('#favIcon')!
		favIcon.href = `assets/${this.assetsFolder}/favicon.svg`
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

	onFilterDropdownWheel(event: WheelEvent) {
		const dropdown = event.currentTarget as HTMLElement
		const target = event.target as HTMLElement
		const list = (target.closest(".filter-dropdown-list") as HTMLElement | null) || dropdown.querySelector(".filter-dropdown-list")
		this.scrollDropdownList(event, list as HTMLElement | null)
	}

	@HostListener("document:click", ["$event"])
	onDocumentClick(event: MouseEvent) {
		const target = event.target as HTMLElement
		if (!target.closest(".chain-filter-container") && this.filterToolbar.chainDropdownOpen) {
			this.filterToolbar.chainDropdownOpen = false
		}
		if (!target.closest(".frontend-filter-container") && this.filterToolbar.frontendDropdownOpen) {
			this.filterToolbar.frontendDropdownOpen = false
		}
	}

	private scrollDropdownList(event: WheelEvent, list: HTMLElement | null) {
		event.stopPropagation()
		if (!list) {
			event.preventDefault()
			return
		}
		const scrollable = list.scrollHeight > list.clientHeight
		if (!scrollable) {
			event.preventDefault()
			return
		}
		const delta =
			event.deltaMode === WheelEvent.DOM_DELTA_LINE
				? event.deltaY * 16
				: event.deltaMode === WheelEvent.DOM_DELTA_PAGE
					? event.deltaY * list.clientHeight
					: event.deltaY
		event.preventDefault()
		list.scrollTop += delta
	}
}
