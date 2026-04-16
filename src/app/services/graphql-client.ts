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
	static readonly REQUEST_TIMEOUT_MS = 10000

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

	private async executeQuery(queryString: string): Promise<any> {
		const controller = new AbortController()
		const timeoutId = setTimeout(() => controller.abort(), GraphQlClient.REQUEST_TIMEOUT_MS)

		try {
			const response = await fetch(this.graphqlUrl, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				signal: controller.signal,
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

			return result.data
		} catch (error) {
			if (error instanceof DOMException && error.name === "AbortError") {
				throw new Error(`GraphQL request timed out after ${GraphQlClient.REQUEST_TIMEOUT_MS / 1000}s`)
			}
			throw error instanceof Error ? error : new Error(String(error))
		} finally {
			clearTimeout(timeoutId)
		}
	}

	private async fetchGraphQL<T>(configs: QueryConfig<T>[]): Promise<{ [method: string]: T[] }> {
		const queryString = this.createGraphQlQuery(configs)
		const resultData = await this.executeQuery(queryString)

		const processedData: { [method: string]: T[] } = {}

		for (const config of configs) {
			let res = (resultData as any)[config.method]
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
			const lastIds: { [method: string]: string | null } = {}

			configs.forEach(config => {
				results[config.method] = []
				loadedPages[config.method] = 0
				startFields[config.method] = startPaginationFields ? startPaginationFields[config.method] : null
				lastIds[config.method] = null
			})

			let continueLoading = true
			while (continueLoading) {
				configs.forEach(config => {
					loadedPages[config.method] += 1
				})

				const updatedConfigs = configs.map(config => {
					const newConfig = { ...config }
					const paginationField = config.orderBy || "timestamp"
					const baseConditions = [...(newConfig.conditions || [])]
					const start = startFields[config.method]

					if (start) {
						baseConditions.push({
							field: paginationField,
							operator: "gte",
							value: start,
						})
					}

					// The entities all use timestamp-prefixed ids, so paging by id gives us a stable
					// unique cursor without double-counting rows that share the same timestamp.
					if (paginationField === "timestamp") {
						newConfig.orderBy = "id"
						const lastId = lastIds[config.method]
						if (lastId) {
							baseConditions.push({
								field: "id",
								operator: "gt",
								value: `"${lastId}"`,
							})
						}
					}

					if (baseConditions.length > 0) {
						newConfig.conditions = baseConditions
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
						if (items.length > 0 && items.length === limit) {
							const lastItem = items[items.length - 1]
							const paginationField = config.orderBy || "timestamp"

							if (paginationField === "timestamp") {
								const nextLastId = (lastItem as any).id
								if (nextLastId == null) {
									throw new Error(`Missing id while paginating ${config.method}`)
								}
								if (nextLastId === lastIds[config.method]) {
									throw new Error(`Pagination cursor did not advance for ${config.method}`)
								}
								lastIds[config.method] = nextLastId
							} else {
								const nextStartField = (lastItem as any)[paginationField]
								if (nextStartField == null) {
									throw new Error(`Missing ${paginationField} while paginating ${config.method}`)
								}
								if (nextStartField === startFields[config.method]) {
									throw new Error(`Pagination cursor did not advance for ${config.method}`)
								}
								startFields[config.method] = nextStartField
							}
						}
					})
				}
			}

			return results
		}

		return from(loadAllData())
	}

	batchLoadAll<T>(
		configSets: { configs: QueryConfig<T>[]; startPaginationFields?: { [method: string]: string | null } }[],
		limit: number = 1000,
	): Observable<{ [method: string]: T[] }[]> {
		const self = this

		async function execute(): Promise<{ [method: string]: T[] }[]> {
			// Prepare configs with initial pagination conditions and alias prefixes
			const aliasedQueries: string[] = []
			const setMeta: { prefix: string; configs: QueryConfig<T>[]; original: (typeof configSets)[0] }[] = []

			configSets.forEach((set, i) => {
				const prefix = `s${i}`
				const prepared = set.configs.map(config => {
					const newConfig = { ...config }
					const start = set.startPaginationFields?.[config.method]
					if (start) {
						newConfig.conditions = [
							...(newConfig.conditions || []),
							{ field: config.orderBy || "timestamp", operator: "gte", value: start },
						]
					}
					return newConfig
				})

				for (const config of prepared) {
					const args = [`first: ${config.first}`]
					if (config.orderBy) args.push(`orderBy: ${config.orderBy}`)
					if (config.conditions && config.conditions.length > 0) {
						const conds = config.conditions.map(c => {
							const op = c.operator ? `_${c.operator}` : ""
							return `${c.field}${op}: ${c.value}`
						})
						args.push(`where: {${conds.join(", ")}}`)
					}
					aliasedQueries.push(`${prefix}_${config.method}: ${config.method}(${args.join(", ")}) { ${config.fields.join("\n")} }`)
				}
				setMeta.push({ prefix, configs: prepared, original: set })
			})

			// Single batched request
			let resultData: any
			self.loadingService.setLoading(true)
			try {
				resultData = await self.executeQuery(`query { ${aliasedQueries.join("\n")} }`)
			} finally {
				self.loadingService.setLoading(false)
			}

			// Parse results by alias prefix
			const batchResults: { [method: string]: T[] }[] = setMeta.map(({ prefix, configs }) => {
				const processed: { [method: string]: T[] } = {}
				for (const config of configs) {
					let res = (resultData as any)[`${prefix}_${config.method}`]
					if (!Array.isArray(res)) res = res != null ? [res] : []
					processed[config.method] = res.map((obj: any) => config.createFunction(obj))
				}
				return processed
			})

			// For sets that hit the page limit, fall back to individual paginated loading
			const finalResults: { [method: string]: T[] }[] = []
			for (let i = 0; i < batchResults.length; i++) {
				const batchResult = batchResults[i]
				const { original } = setMeta[i]

				const needsPagination = original.configs.some(config => (batchResult[config.method]?.length || 0) >= limit)

				if (needsPagination) {
					const fullResult = await lastValueFrom(
						self.loadAll(original.configs, limit, original.startPaginationFields).pipe(take(1)),
					)
					finalResults.push(fullResult)
				} else {
					finalResults.push(batchResult)
				}
			}

			return finalResults
		}

		return from(execute())
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
