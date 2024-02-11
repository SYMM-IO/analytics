import {Injectable} from '@angular/core'
import {HttpClient} from "@angular/common/http"
import {EnvironmentInterface} from "../../environments/environment-interface"
import {map} from "rxjs/operators"
import {AffiliateSnapshot, HedgerSnapshot} from "../models"
import {catchError, Observable} from "rxjs"

@Injectable({
	providedIn: 'root',
})
export class SnapshotService {

	constructor(readonly httpClient: HttpClient) {

	}

	loadHedgerSnapshot(env: EnvironmentInterface, hedger: string): Observable<HedgerSnapshot> {
		return this.httpClient.get(`${env.serverUrl}/snapshots/hedger/${env.name}/${hedger}`)
			.pipe(
				map(value => HedgerSnapshot.fromRawObject(value)),
			)
	}

	loadAffiliateSnapshot(env: EnvironmentInterface, affiliate: string): Observable<AffiliateSnapshot> {
		return this.httpClient.get(`${env.serverUrl}/snapshots/affiliate/${env.name}/${affiliate}`)
			.pipe(map(value => AffiliateSnapshot.fromRawObject(value)))
	}
}
