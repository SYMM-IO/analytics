import { Apollo, gql } from "apollo-angular"
import { from, interval, lastValueFrom, Observable, take } from "rxjs"
import { map, startWith, switchMap } from "rxjs/operators"
import { LoadingService } from "./Loading.service"
import { Logger } from "@angular-devkit/core/src/logger"

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
		private apollo: Apollo,
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

	private load<T>(configs: QueryConfig<T>[]): Observable<{ [method: string]: T[] }> {
		const queryString = this.createGraphQlQuery(configs)
		const graphQLQuery = gql`
			${queryString}
		`
		this.loadingService.setLoading(true)

		return this.apollo
			.watchQuery({
				query: graphQLQuery,
				fetchPolicy: "network-only",
			})
			.valueChanges.pipe(
				map(({ data }) => {
					this.loadingService.setLoading(false)
					const processedData: { [method: string]: T[] } = {}

					for (const config of configs) {
						let res = (data as any)[config.method]
						if (!Array.isArray(res)) res = [res]
						processedData[config.method] = res.map((obj: any) => config.createFunction(obj))
					}
					return processedData
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
