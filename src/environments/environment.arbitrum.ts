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

export const carbonMultiAccount: Affiliate = {
	name: AffiliateName.CARBON,
	mainColor: affiliateColors.get(AffiliateName.CARBON),
	address: "0xbc029264eb164f36D7DfEfc46A607b66C2b4F379",
	fromTimestamp: "0",
}

export const carbonAccountLayer: Affiliate = {
	name: AffiliateName.CARBON,
	mainColor: affiliateColors.get(AffiliateName.CARBON),
	address: "0x5560266516865cd55460f3ab94c61d78e48d3d92",
	fromTimestamp: "0",
}

// Deposits and Traded Volume intentionally retain the frontend population used
// before symmioEntities became the source for chart and filter entities.
export const legacyCarbonAffiliate: Affiliate = {
	name: AffiliateName.CARBON,
	mainColor: affiliateColors.get(AffiliateName.CARBON),
	address: "0xd600A4F314D3F1ee8869A340D298a69Ff070E574",
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

export const carbonSolver: Solver = {
	name: SolverName.CARBON,
	address: "0xd600A4F314D3F1ee8869A340D298a69Ff070E574",
	mainColor: solverColors.get(SolverName.CARBON),
}

export const carbonSolver2: Solver = {
	name: SolverName.CARBON,
	address: "0xe72284fc2D56bE2C1649742FD131BceA41A94a6a",
	mainColor: solverColors.get(SolverName.CARBON),
}

export const environment: EnvironmentInterface = {
	name: "ARBITRUM",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/arbitrum_analytics/latest/gn",
	collateralDecimal: 6,
	collaterals: ["0xaf88d065e77c8cC2239327C5EDb3A432268e5831"],
	version: Version.LATEST,
	startDate: new Date(1715990400000),
	affiliates: [pear, intentx, cloverfield, xpanse, carbonMultiAccount, carbonAccountLayer, NULL_AFFILIATE],
	legacyMetricAffiliates: [pear, intentx, cloverfield, xpanse, legacyCarbonAffiliate, NULL_AFFILIATE],
	solvers: [perps1, perps2, perps3, carbonSolver, carbonSolver2],
}
