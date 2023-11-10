import {Injectable} from '@angular/core'
import {BehaviorSubject, Subject} from "rxjs"

@Injectable({
	providedIn: 'root'
})
export class StateService {
	public nightMode: Subject<boolean> = new BehaviorSubject<boolean>(true)

	constructor() {
	}
}
