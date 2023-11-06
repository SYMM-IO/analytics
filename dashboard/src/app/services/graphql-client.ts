import {Apollo, gql} from "apollo-angular"
import {defer, interval, Observable} from "rxjs"
import {expand, map, startWith, switchMap} from "rxjs/operators"
import {LoadingService} from "./Loading.service"

export interface Condition {
	field: string;
	operator: string;
	value: string;
}

export interface Query {
	method: string;
	query: string;
	createFunction: (obj: any) => any;
}

export class GraphQlClient {

	constructor(private apollo: Apollo, private loadingService: LoadingService) {
	}

	createGraphQlQuery(
		method: string,
		fields: string[],
		first: number,
		conditions: Condition[] = [],
		orderBy?: string
	): any {
		return `${method}(
          first: ${first},
          ${orderBy ? `orderBy: ${orderBy}` : ""}
          ${conditions.length > 0
			? `where: {${conditions
				.map((c) => `${c.field}${c.operator.length > 0 ? "_" : ""}${c.operator}: ${c.value}`)
				.join(", ")}}`
			: ""
		}
        ) {
          ${fields.map((field) => field).join(", \n")}
        }`
	}

    load(queries: Query[]): Observable<any> {
        const q = gql`query q {
            ${queries.map((q) => q.query).join(", ")}
        }`
		this.loadingService.setLoading(true)
		return this.apollo
			.watchQuery({
				query: q,
				fetchPolicy: 'network-only'  // Disable caching here
			})
			.valueChanges.pipe(
				map(({data, loading}) => {
					this.loadingService.setLoading(false)
					let processedData: any = {}
					for (const query of queries) {
						processedData[query.method] = (data as any)[query.method].map(
							(obj: any) => query.createFunction(obj)
						)
					}
					return processedData
				})
			)
    }

	loadAll<T>(
		method: string,
		fields: string[],
		paginationField: string,
		createFunction: (obj: any) => any,
		conditions: Condition[] = [],
		startPaginationField: string | null = null,
		pageLimit: number | undefined = undefined
	): Observable<T[]> {
		const limit = 1000

		let outer = this
		let loadedPages = 0
		const loadPage = (start: string | null): Observable<any[]> => {
			loadedPages++
			const c = [...conditions]
			if (start) {
				c.push({field: paginationField, operator: "gte", value: start})
			}
			return this.load([
				{
					query: outer.createGraphQlQuery(
						method,
						fields,
						limit,
						c,
						paginationField
					),
					method: method,
					createFunction: createFunction,
				},
			]).pipe(
				map((result: any) =>
					result[method].filter(
						(item: T) => (item as any)[paginationField] !== start
					)
				),
				expand((items: T[]) =>
					items.length === limit &&
					(pageLimit == null || loadedPages < pageLimit)
						? loadPage((items[items.length - 1] as any)[paginationField])
						: []
				)
			)
		}

		return defer(() => loadPage(startPaginationField))
	}


	loadAllWithInterval<T>(
		method: string,
		fields: string[],
		paginationField: string,
		createFunction: (obj: any) => any,
		conditions: Condition[] = [],
		startPaginationField: string | null = null,
		pageLimit: number | undefined = undefined,
		fetchInterval: number = 30000
	): Observable<T[]> {
		return interval(fetchInterval)
			.pipe(
				startWith(0), // To trigger an immediate fetch
				switchMap(() => this.loadAll<T>(
					method,
					fields,
					paginationField,
					createFunction,
					conditions,
					startPaginationField,
					pageLimit
				))
			)
	}
}
