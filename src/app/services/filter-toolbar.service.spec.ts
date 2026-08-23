import { FilterToolbarService } from "./filter-toolbar.service"

describe("FilterToolbarService", () => {
	it("formats the frontend sorting volume for the development dropdown", () => {
		const service = new FilterToolbarService()
		service.setFrontendVolumes(new Map([["Privex", "1234567890000000000000000000"]]))

		expect(service.frontendVolume("Privex")).toBe("$1.23B")
		expect(service.frontendVolume("Missing")).toBe("—")
		expect(service.hasFrontendTradeVolume("Privex")).toBeTrue()
		expect(service.hasFrontendTradeVolume("Missing")).toBeFalse()
	})

	it("does not treat an explicit zero as frontend trade volume", () => {
		const service = new FilterToolbarService()
		service.setFrontendVolumes(new Map([["Zero", "0"]]))

		expect(service.hasFrontendTradeVolume("Zero")).toBeFalse()
	})

	it("groups positive frontend volumes below $100K into Others", () => {
		const service = new FilterToolbarService()
		const usd = (value: number) => BigInt(value) * 10n ** 18n
		service.setFrontendVolumes(
			new Map([
				["Low A", usd(60_000).toString()],
				["Low B", usd(40_000).toString()],
				["At threshold", usd(100_000).toString()],
				["Zero", "0"],
			]),
		)

		expect(service.frontendDisplayName("Low A")).toBe("Others")
		expect(service.frontendDisplayName("Low B")).toBe("Others")
		expect(service.frontendDisplayName("At threshold")).toBe("At threshold")
		expect(service.frontendDisplayName("Zero")).toBe("Zero")
		expect(service.frontendVolume("Others")).toBe("$100K")
		expect(service.hasFrontendTradeVolume("Others")).toBeTrue()
		expect(service.hasFrontendTradeVolume("Low A")).toBeFalse()
	})
})
