import { Inject, Injectable, InjectionToken, Optional } from "@angular/core"
import {
	Affiliate,
	affiliateColors,
	EnvironmentInterface,
	Solver,
	solverColors,
	SolverName,
	SymmioEntity,
} from "../../environments/environment-interface"
import { BehaviorSubject } from "rxjs"

export const ENVIRONMENT = new InjectionToken<{ [key: string]: any }>("environment")

const ENTITY_QUERY = `
	query AnalyticsEntities {
		symmioEntities(first: 1000) {
			address
			type
			name
			brandColor
		}
	}
`
const ENTITY_LOAD_TIMEOUT_MS = 10000
const NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
const UNKNOWN_NAME = "Unknown"
const ENTITY_NAME_ALIASES = new Map([["agentsolver", SolverName.PRIVEX]])
const SOLVER_NAME_OVERRIDES_BY_ADDRESS = new Map([["0xe72284fc2d56be2c1649742fd131bcea41a94a6a", SolverName.CARBON]])
const FALLBACK_COLORS = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", "#3ba272", "#fc8452", "#9a60b4"]

@Injectable({
	providedIn: "root",
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
		for (const env of this.environments) {
			env.legacyMetricAffiliates ??= [...(env.affiliates ?? [])]
		}
		this.selectedEnvironment.next(this.environments[this.environments.length - 1])
	}

	getValue(key: string, defaultValue?: any): any {
		return this.environment[key] || defaultValue
	}

	async initializeEntities(): Promise<void> {
		await Promise.all(this.environments.map(env => this.loadEntities(env)))
		this.selectedEnvironment.next(this.environments[this.environments.length - 1])
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

	private async loadEntities(env: EnvironmentInterface): Promise<void> {
		if (!env.subgraphUrl) return

		const fallbackAffiliates = env.affiliates ?? []
		const fallbackSolvers = env.solvers ?? []
		const controller = new AbortController()
		const timeoutId = setTimeout(() => controller.abort(), ENTITY_LOAD_TIMEOUT_MS)

		try {
			const response = await fetch(env.subgraphUrl, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				signal: controller.signal,
				body: JSON.stringify({ query: ENTITY_QUERY }),
			})
			if (!response.ok) throw new Error(`GraphQL request failed: ${response.status}`)

			const result = (await response.json()) as {
				data?: { symmioEntities?: SymmioEntity[] }
				errors?: unknown[]
			}
			if (result.errors || !Array.isArray(result.data?.symmioEntities)) {
				throw new Error("symmioEntities is unavailable")
			}

			const entities = result.data.symmioEntities
			const affiliates = entities.filter(entity => entity.type === "Affiliate").map(entity => this.toAffiliate(entity, fallbackAffiliates))
			const solvers = entities.filter(entity => entity.type === "Solver").map(entity => this.toSolver(entity, fallbackSolvers))

			const localAffiliateOverrides = fallbackAffiliates.filter(affiliate => affiliate.address?.toLowerCase() === NULL_ADDRESS)
			env.affiliates = this.mergeByAddress(affiliates, localAffiliateOverrides)
			env.solvers = solvers
		} catch (error) {
			console.warn(`Using configured entities for ${env.name}:`, error)
		} finally {
			clearTimeout(timeoutId)
		}
	}

	private toAffiliate(entity: SymmioEntity, fallbackAffiliates: Affiliate[]): Affiliate {
		const existing = this.findByAddress(fallbackAffiliates, entity.address)
		const name = this.resolveName(entity.name)
		return {
			name,
			address: entity.address,
			mainColor: this.resolveColor(name, entity.brandColor, existing?.mainColor, affiliateColors),
			fromTimestamp: existing?.fromTimestamp ?? "0",
			depositDiff: existing?.depositDiff,
		}
	}

	private toSolver(entity: SymmioEntity, fallbackSolvers: Solver[]): Solver {
		const existing = this.findByAddress(fallbackSolvers, entity.address)
		const name = SOLVER_NAME_OVERRIDES_BY_ADDRESS.get(entity.address.toLowerCase()) ?? this.resolveName(entity.name)
		return {
			name,
			address: entity.address,
			mainColor: this.resolveColor(name, entity.brandColor, existing?.mainColor, solverColors),
		}
	}

	private resolveName(name: string | null): string {
		const normalizedName = name?.trim()
		if (!normalizedName) return UNKNOWN_NAME
		return ENTITY_NAME_ALIASES.get(normalizedName.toLowerCase()) ?? normalizedName
	}

	private resolveColor(name: string, brandColor: string | null, existingColor: string | undefined, colors: Map<string, string>): string {
		const configured = [...colors.entries()].find(([key]) => key.toLowerCase() === name.toLowerCase())?.[1]
		return configured ?? existingColor ?? brandColor ?? this.fallbackColor(name)
	}

	private fallbackColor(value: string): string {
		let hash = 0
		for (let index = 0; index < value.length; index++) hash = (hash * 31 + value.charCodeAt(index)) | 0
		return FALLBACK_COLORS[Math.abs(hash) % FALLBACK_COLORS.length]
	}

	private findByAddress<T extends { address?: string }>(items: T[], address: string): T | undefined {
		const normalizedAddress = address.toLowerCase()
		return items.find(item => item.address?.toLowerCase() === normalizedAddress)
	}

	private mergeByAddress<T extends { address?: string }>(primary: T[], overrides: T[]): T[] {
		const items = new Map(primary.map(item => [item.address?.toLowerCase(), item]))
		for (const override of overrides) {
			const key = override.address?.toLowerCase()
			if (!items.has(key)) items.set(key, override)
		}
		return [...items.values()]
	}
}
