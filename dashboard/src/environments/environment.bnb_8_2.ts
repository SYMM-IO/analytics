import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"


export const alpha_v3: Affiliate = {
	name: "Thena",
	mainColor: "#ED00C9",
	accountSource: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
	fromTimestamp: null,
}

export const cloverfield: Affiliate = {
	name: "Cloverfield",
	mainColor: "#A2D4EA",
	accountSource: "0xcCc8CC82868B94Bc2759c69375fC7Ae769703EB8",
	fromTimestamp: "0",
}

export const hedger: Hedger = {
	name: "Thena_Hedger",
}

export const hedger2: Hedger = {
	name: "Orbs_Hedger",
}

export const environment: EnvironmentInterface = {
	name: "BNB_8_2",
	serverUrl: "https://analytics-api.symm.io",
	assetsFolder: "thena",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/bnb_analytics/latest/gn",
	collateralDecimal: 18,
	version: Version.V_0_8_2,
	startDate: new Date(1702058147000),
	affiliates: [
		alpha_v3,
		cloverfield
	],
	hedgers: [
		hedger,
		hedger2,
	],
}

