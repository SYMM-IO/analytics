import { firstValueFrom } from "rxjs"
import { LoadingService } from "./Loading.service"
import { GraphQlClient, QueryConfig } from "./graphql-client"

describe("GraphQlClient", () => {
	it("does not append a completed query again while another query keeps paginating", async () => {
		const loadingService = { setLoading: () => undefined } as unknown as LoadingService
		const client = new GraphQlClient("https://example.test/graphql", loadingService)
		const dailyRows = [
			{ id: "1_daily", timestamp: "1" },
			{ id: "2_daily", timestamp: "2" },
		]
		const totalRow = { id: "total_1", timestamp: "1" }

		spyOn(window, "fetch").and.callFake(async (_input, init) => {
			const query = (JSON.parse(String(init?.body)) as { query: string }).query
			const dailyHasCursor = /dailyHistories\([^)]*id_gt/.test(query)
			const totalHasCursor = /totalHistories\([^)]*id_gt/.test(query)

			return new Response(
				JSON.stringify({
					data: {
						dailyHistories: dailyHasCursor ? [] : dailyRows,
						totalHistories: totalHasCursor ? [] : [totalRow],
					},
				}),
				{ status: 200, headers: { "Content-Type": "application/json" } },
			)
		})

		const config = (method: string): QueryConfig<{ id: string; timestamp: string }> => ({
			method,
			fields: ["id", "timestamp"],
			first: 2,
			orderBy: "timestamp",
			createFunction: value => value,
		})

		const result = await firstValueFrom(client.loadAll([config("dailyHistories"), config("totalHistories")], 2))

		expect(result["dailyHistories"]).toEqual(dailyRows)
		expect(result["totalHistories"]).toEqual([totalRow])
		expect(window.fetch).toHaveBeenCalledTimes(2)
	})

	it("can reproduce the legacy main-branch pagination for compatibility metrics", async () => {
		const loadingService = { setLoading: () => undefined } as unknown as LoadingService
		const client = new GraphQlClient("https://example.test/graphql", loadingService)
		const dailyRows = [
			{ id: "1_daily", timestamp: "1" },
			{ id: "2_daily", timestamp: "2" },
		]
		const totalRow = { id: "total_1", timestamp: "1" }

		spyOn(window, "fetch").and.callFake(async (_input, init) => {
			const query = (JSON.parse(String(init?.body)) as { query: string }).query
			const dailyHasCursor = /dailyHistories\([^)]*id_gt/.test(query)

			return new Response(
				JSON.stringify({
					data: {
						dailyHistories: dailyHasCursor ? [] : dailyRows,
						totalHistories: [totalRow],
					},
				}),
				{ status: 200, headers: { "Content-Type": "application/json" } },
			)
		})

		const config = (method: string): QueryConfig<{ id: string; timestamp: string }> => ({
			method,
			fields: ["id", "timestamp"],
			first: 2,
			orderBy: "timestamp",
			createFunction: value => value,
		})

		const result = await firstValueFrom(
			client.loadAll(
				[config("dailyHistories"), config("totalHistories")],
				2,
				undefined,
				undefined,
				{ advancePartialPageCursors: false },
			),
		)

		expect(result["dailyHistories"]).toEqual(dailyRows)
		expect(result["totalHistories"]).toEqual([totalRow, totalRow])
		expect(window.fetch).toHaveBeenCalledTimes(2)
	})
})
