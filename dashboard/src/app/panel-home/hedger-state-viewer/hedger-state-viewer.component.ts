import {Component, Input} from '@angular/core'
import {Hedger} from "../../../environments/environment-interface"
import {HedgerSnapshot} from "../../models"

@Component({
	selector: 'hedger-state-viewer',
	templateUrl: './hedger-state-viewer.component.html',
	styleUrl: './hedger-state-viewer.component.scss',
})
export class HedgerStateViewerComponent {

	@Input() hedgerSnapshot!: HedgerSnapshot | undefined
	@Input() hedger!: Hedger

	constructor() {

	}

}
