import {Injectable} from "@angular/core"
import {BehaviorSubject, Observable} from "rxjs"

@Injectable({
	providedIn: "root",
})
export class LoadingService {
	private loading: BehaviorSubject<boolean> = new BehaviorSubject<boolean>(
		false
	)

	public loading$(): Observable<boolean> {
		return this.loading.asObservable()
	}

	public setLoading(b: boolean) {
		this.loading.next(b)
	}
}
