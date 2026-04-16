import {Inject, Injectable, InjectionToken, Optional} from "@angular/core"
import {EnvironmentInterface} from "../../environments/environment-interface"
import {BehaviorSubject} from "rxjs"

export const ENVIRONMENT = new InjectionToken<{ [key: string]: any }>('environment')

@Injectable({
	providedIn: 'root',
})
export class EnvironmentService {
	private readonly environment: any
	private readonly ignoredSubgraphs = new Set<string>()
	private readonly loadedSubgraphNames = new Set<string>()
	public readonly environments: any[]
	public readonly loadedSubgraphs = new BehaviorSubject<string[]>([])
	public readonly ignoredSubgraphNames = new BehaviorSubject<string[]>([])
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

	markSubgraphIgnored(environmentName: string): boolean {
		if (this.ignoredSubgraphs.has(environmentName)) return false
		this.ignoredSubgraphs.add(environmentName)
		this.loadedSubgraphNames.delete(environmentName)
		this.loadedSubgraphs.next(this.environments.map(env => env.name).filter(name => this.loadedSubgraphNames.has(name)))
		this.ignoredSubgraphNames.next(this.environments.map(env => env.name).filter(name => this.ignoredSubgraphs.has(name)))
		return true
	}

	markSubgraphLoaded(environmentName: string): boolean {
		if (this.loadedSubgraphNames.has(environmentName)) return false
		this.loadedSubgraphNames.add(environmentName)
		this.ignoredSubgraphs.delete(environmentName)
		this.loadedSubgraphs.next(this.environments.map(env => env.name).filter(name => this.loadedSubgraphNames.has(name)))
		this.ignoredSubgraphNames.next(this.environments.map(env => env.name).filter(name => this.ignoredSubgraphs.has(name)))
		return true
	}
}
