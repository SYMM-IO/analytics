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

export const vibe: Affiliate = {
	name: AffiliateName.VIBE,
	mainColor: affiliateColors.get(AffiliateName.VIBE),
	address: "0xBcB033C9154401fA000a1Ae60843f79f45741b7c",
	fromTimestamp: "0",
}

export const superflow: Solver = {
	name: SolverName.SUPERFLOW,
	address: "0x76bc5889c0cfcC20960b0D81F541595d81a95122",
	mainColor: solverColors.get(SolverName.SUPERFLOW),
}

export const environment: EnvironmentInterface = {
	name: "HyperEVM",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/hyperevm_mainnet_analytics/latest/gn",
	collateralDecimal: 6,
	collaterals: ["0xb88339CB7199b77E23DB6E890353E22632Ba630f"],
	version: Version.LATEST,
	affiliates: [vibe, NULL_AFFILIATE],
	solvers: [superflow],
}
