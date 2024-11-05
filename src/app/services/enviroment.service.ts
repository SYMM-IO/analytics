import {Inject, Injectable, InjectionToken, Optional} from "@angular/core"
import {EnvironmentInterface} from "../../environments/environment-interface"
import {BehaviorSubject, Observable} from "rxjs"

export const ENVIRONMENT = new InjectionToken<{ [key: string]: any }>('environment')

@Injectable({
	providedIn: 'root',
})
export class EnvironmentService {
	private readonly environment: any
	public readonly environments: any[]
	public readonly selectedEnvironment = new BehaviorSubject<EnvironmentInterface | null>(null)

	// We need @Optional to be able to start app without providing environment file
	constructor(@Optional() @Inject(ENVIRONMENT) environment: any) {
		this.environment = environment !== null ? environment : {}
		this.environments = this.getValue("environments")
		this.selectedEnvironment.next(this.environments[this.environments.length - 1])
	}

	getValue(key: string, defaultValue?: any): any {
		return this.environment[key] || defaultValue
	}
}