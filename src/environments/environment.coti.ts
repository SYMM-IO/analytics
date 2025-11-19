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

export const privex: Affiliate = {
	name: AffiliateName.PRIVEX,
	mainColor: affiliateColors.get(AffiliateName.PRIVEX),
	address: "0xbF318724218cED9A3ff7CfC642c71a0CA1952b0F",
	fromTimestamp: "0",
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x61109a6eb070a860b1da2a38f93ca2b884b54f90",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const privex_solver: Solver = {
	name: SolverName.PRIVEX,
	address: "0xb6e3b44975f2966707a91747f89d2002ff8d62db",
	mainColor: solverColors.get(SolverName.PRIVEX),
}

export const environment: EnvironmentInterface = {
	name: "Coti",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://graph-symmio.prvx.io/subgraphs/name/coti-perps-analytics",
	collateralDecimal: 6,
	collaterals: ["0xf1Feebc4376c68B7003450ae66343Ae59AB37D3C"],
	version: Version.LATEST,
	startDate: new Date(1743595930000),
	affiliates: [privex, NULL_AFFILIATE],
	solvers: [perps1_solver, privex_solver],
}
