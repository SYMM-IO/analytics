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

export const ivx: Affiliate = {
	name: AffiliateName.IVX,
	mainColor: affiliateColors.get(AffiliateName.IVX),
	address: "0x5C9fc09b120B7333F1DCf644C7665cEdea3dc7e2",
	fromTimestamp: null,
}

export const lode: Affiliate = {
	name: AffiliateName.LODE,
	mainColor: affiliateColors.get(AffiliateName.LODE),
	address: "0x703c4927945Aac2B5a76f4c1D85Bc85e6fAaddB6",
	fromTimestamp: "0",
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xdfeD11fE4af63B059EDBBDf53e9C633B331ed432",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps2_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x78B1b8134A4236e69aE3728691e90B31f02C3001",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x8141c1840F7D190Cd24239C22b1e560e08999B12",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "Bera",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/bera_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0xFCBD14DC51f0A4d49d5E53C2E0950e0bC26d0Dce"],
	version: Version.LATEST,
	startDate: new Date(1738658091000),
	affiliates: [ivx, NULL_AFFILIATE],
	solvers: [perps1_solver, perps2_solver, perps3_solver],
}
