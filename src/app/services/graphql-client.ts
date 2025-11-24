import { from, interval, lastValueFrom, Observable, take, throwError } from "rxjs"
import { catchError, map, startWith, switchMap } from "rxjs/operators"
import { LoadingService } from "./Loading.service"

export interface Condition {
	field: string
	operator: string
	value: string
}

export interface QueryConfig<T> {
	method: string
	fields: string[]
	first: number
	conditions?: Condition[]
	orderBy?: string
	createFunction: (obj: any) => T
}

export class GraphQlClient {
	constructor(
		private graphqlUrl: string,
		private loadingService: LoadingService,
	) {}

	private createGraphQlQuery(configs: QueryConfig<any>[]): string {
		const methodsQueries = configs.map(config => {
			const args = [`first: ${config.first}`]

			if (config.orderBy) {
				args.push(`orderBy: ${config.orderBy}`)
			}

			if (config.conditions && config.conditions.length > 0) {
				const conditionStrings = config.conditions.map(c => {
					const operatorSuffix = c.operator ? `_${c.operator}` : ""
					return `${c.field}${operatorSuffix}: ${c.value}`
				})
				args.push(`where: {${conditionStrings.join(", ")}}`)
			}

			const argsString = args.join(", ")
			const fieldsString = config.fields.join("\n")

			return `
        ${config.method}(${argsString}) {
          ${fieldsString}
        }
      `
		})

		return `
      query {
        ${methodsQueries.join("\n")}
      }
    `
	}

	private async fetchGraphQL<T>(configs: QueryConfig<T>[]): Promise<{ [method: string]: T[] }> {
		const queryString = this.createGraphQlQuery(configs)

		const response = await fetch(this.graphqlUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				query: queryString,
			}),
		})

		if (!response.ok) {
			throw new Error(`GraphQL request failed: ${response.status} ${response.statusText}`)
		}

		const result = await response.json()

		if (result.errors) {
			throw new Error(`GraphQL errors: ${JSON.stringify(result.errors)}`)
		}

		const processedData: { [method: string]: T[] } = {}

		for (const config of configs) {
			let res = (result.data as any)[config.method]
			if (!Array.isArray(res)) res = [res]
			processedData[config.method] = res.map((obj: any) => config.createFunction(obj))
		}

		return processedData
	}

	private load<T>(configs: QueryConfig<T>[]): Observable<{ [method: string]: T[] }> {
		this.loadingService.setLoading(true)

		return from(this.fetchGraphQL<T>(configs)).pipe(
			map(data => {
				this.loadingService.setLoading(false)
				return data
			}),
			catchError(error => {
				this.loadingService.setLoading(false)
				return throwError(() => error)
			}),
		)
	}

	loadAll<T>(
		configs: QueryConfig<T>[],
		limit: number = 1000,
		startPaginationFields?: { [method: string]: string | null },
		pageLimits?: { [method: string]: number },
	): Observable<{ [method: string]: T[] }> {
		const self = this

		async function loadAllData(): Promise<{ [method: string]: T[] }> {
			const results: { [method: string]: T[] } = {}
			const loadedPages: { [method: string]: number } = {}
			const startFields: { [method: string]: string | null } = {}

			configs.forEach(config => {
				results[config.method] = []
				loadedPages[config.method] = 0
				startFields[config.method] = startPaginationFields ? startPaginationFields[config.method] : null
			})

			let continueLoading = true
			while (continueLoading) {
				configs.forEach(config => {
					loadedPages[config.method] += 1
				})

				const updatedConfigs = configs.map(config => {
					const newConfig = { ...config }
					const start = startFields[config.method]
					if (start) {
						const paginationCondition: Condition = {
							field: config.orderBy || "timestamp",
							operator: "gte",
							value: start,
						}
						newConfig.conditions = [...(newConfig.conditions || []), paginationCondition]
					}
					return newConfig
				})

				const result = await lastValueFrom(self.load<T>(updatedConfigs).pipe(take(1)))
				configs.forEach(config => {
					const items = result[config.method]
					results[config.method] = results[config.method].concat(items)
				})

				continueLoading = configs.some(config => {
					const items = result[config.method]
					const hasMoreItems = items.length === limit
					const withinPageLimit = !pageLimits || !pageLimits[config.method] || loadedPages[config.method] < pageLimits[config.method]
					return hasMoreItems && withinPageLimit
				})

				if (continueLoading) {
					configs.forEach(config => {
						const items = result[config.method]
						if (items.length > 0) {
							const lastItem = items[items.length - 1]
							startFields[config.method] = (lastItem as any)[config.orderBy || "timestamp"]
						} else {
							startFields[config.method] = null
						}
					})
				}
			}

			return results
		}

		return from(loadAllData())
	}

	loadAllWithInterval<T>(
		configs: QueryConfig<T>[],
		fetchInterval: number = 30000,
		limit: number = 1000,
		startPaginationFields?: { [method: string]: string | null },
		pageLimits?: { [method: string]: number },
	): Observable<{ [method: string]: T[] }> {
		return interval(fetchInterval).pipe(
			startWith(0),
			switchMap(() => this.loadAll<T>(configs, limit, startPaginationFields, pageLimits)),
		)
	}
}
