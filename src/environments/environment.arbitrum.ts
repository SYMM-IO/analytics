import {
	Affiliate,
	affiliateColors,
	AffiliateName,
	EnvironmentInterface,
	NULL_AFFILIATE,
	Solver,
	solverColors,
	SolverName,
	Version,
} from "./environment-interface"

export const pear: Affiliate = {
	name: AffiliateName.PEAR,
	mainColor: affiliateColors.get(AffiliateName.PEAR),
	address: "0x6273242a7E88b3De90822b31648C212215caaFE4",
	fromTimestamp: "0",
}

export const intentx: Affiliate = {
	name: AffiliateName.INTENTX,
	mainColor: affiliateColors.get(AffiliateName.INTENTX),
	address: "0x141269E29a770644C34e05B127AB621511f20109",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0x6a3C63Ed5e558a4c4810ecC980ba6075476602D6",
	fromTimestamp: "0",
}

export const xpanse: Affiliate = {
	name: AffiliateName.XPANSE,
	mainColor: affiliateColors.get(AffiliateName.XPANSE),
	address: "0x263A8220e9351c5d0cC13567Db4d7BF58e7470c6",
	fromTimestamp: "0",
}

export const perps1: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x00c069d68bc7420740460dbc3cc3fff9b3742421",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps2: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x7d387771f6e23f353a4afce21af521875c0825d0",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xdb91d232e93969130272de309d3d914547604426",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "ARBITRUM",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cmi1t9ac85xtt01zf0gpn0sw1/subgraphs/arbitrum_analytics/latest/gn",
	collateralDecimal: 6,
	collaterals: ["0xaf88d065e77c8cC2239327C5EDb3A432268e5831"],
	version: Version.LATEST,
	startDate: new Date(1715990400000),
	affiliates: [pear, intentx, cloverfield, xpanse, NULL_AFFILIATE],
	solvers: [perps1, perps2, perps3],
}
