import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const alpha_v3: Affiliate = {
	name: "Thena",
	mainColor: "#ED00C9",
	accountSource: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
	fromTimestamp: null,
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
	subgraphUrl: "https://api.studio.thegraph.com/query/62454/analytics_bnb_8_2/version/latest",
	collateralDecimal: 18,
	startDate: new Date(1702058147000),
	affiliates: [
		alpha_v3,
	],
	hedgers: [
		hedger,
		hedger2,
	],
}

