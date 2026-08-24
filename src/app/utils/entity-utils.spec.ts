import { EnvironmentInterface } from "../../environments/environment-interface"
import { resolveAffiliate } from "./entity-utils"

describe("resolveAffiliate", () => {
	function environment(): EnvironmentInterface {
		return { name: "test", affiliates: [] }
	}

	it("uses the Trading SDK fallback name", () => {
		expect(resolveAffiliate(environment(), "0x45EECD7B4F442388ACD90467E423A5CAAC3A9C3F").name).toBe("Trading SDK")
	})

	it("uses the Echoes fallback name", () => {
		expect(resolveAffiliate(environment(), "0xa503eb7714d4328f3d425f24954c6f5f00115e09").name).toBe("Echoes")
	})

	it("uses the Bulla fallback name", () => {
		expect(resolveAffiliate(environment(), "0xBb1AD4e9430eB87516774E0079B1529E079A0596").name).toBe("Bulla")
	})

	it("keeps Unknown for an unregistered address", () => {
		expect(resolveAffiliate(environment(), "0x1111111111111111111111111111111111111111").name).toBe("Unknown")
	})

	it("keeps a subgraph-provided affiliate name", () => {
		const env = environment()
		env.affiliates = [
			{
				name: "Registered name",
				address: "0x45eecd7b4f442388acd90467e423a5caac3a9c3f",
				fromTimestamp: "0",
			},
		]

		expect(resolveAffiliate(env, "0x45EECD7B4F442388ACD90467E423A5CAAC3A9C3F").name).toBe("Registered name")
	})
})
