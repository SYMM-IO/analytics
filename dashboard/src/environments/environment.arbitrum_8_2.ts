import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"


export const pear: Affiliate = {
	name: "Pear",
	mainColor: "#ace075",
	accountSource: "0x6273242a7E88b3De90822b31648C212215caaFE4",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: "Cloverfield",
	mainColor: "#A2D4EA",
	accountSource: "0x6a3C63Ed5e558a4c4810ecC980ba6075476602D6",
	fromTimestamp: "0",
}

export const hedger: Hedger = {
	name: "arbitrum_Hedger",
}

export const environment: EnvironmentInterface = {
	name: "ARBITRUM_8_2",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/arbitrum_analytics/latest/gn",
	collateralDecimal: 6,
	version: Version.V_0_8_2,
	startDate: new Date(1715990400000),
	affiliates: [
		pear,
		cloverfield
	],
	hedgers: [
		hedger,
	],
}

