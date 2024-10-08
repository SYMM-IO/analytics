import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"


export const intentX: Affiliate = {
	name: "IntentX",
	mainColor: "#F20C27",
	accountSource: "0xECbd0788bB5a72f9dFDAc1FFeAAF9B7c2B26E456",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: "Cloverfield",
	mainColor: "#A2D4EA",
	accountSource: "0xfA8A07fcB6204Ce2229C244a26F42563A72f369E",
	fromTimestamp: "0",
}

export const hedger: Hedger = {
	name: "Mantle_Hedger",
}

export const environment: EnvironmentInterface = {
	name: "MANTLE_8_2",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/mantle_analytics/latest/gn",
	collateralDecimal: 18,
	version: Version.V_0_8_2,
	startDate: new Date(1712075812000),
	affiliates: [
		intentX,
		cloverfield
	],
	hedgers: [
		hedger,
	],
}

