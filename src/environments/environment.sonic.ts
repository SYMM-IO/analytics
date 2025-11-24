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

export const spooky: Affiliate = {
	name: AffiliateName.SPOOKY,
	mainColor: affiliateColors.get(AffiliateName.SPOOKY),
	address: "0xd90ACA50eE8Cb7C3dD1fEe84A722d574186cdd17",
	fromTimestamp: "0",
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x7D387771f6E23f353a4afCE21af521875C0825D0",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "Sonic",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cmi1t9ac85xtt01zf0gpn0sw1/subgraphs/sonic_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x29219dd400f2Bf60E5a23d13Be72B486D4038894"],
	version: Version.LATEST,
	startDate: new Date(1750809600000),
	affiliates: [spooky, NULL_AFFILIATE],
	solvers: [perps1_solver],
}
