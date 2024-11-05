import { Affiliate, affiliateColors, AffiliateName, EnvironmentInterface, Solver, solverColors, SolverName, Version } from "./environment-interface"

export const alpha_v3: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
	fromTimestamp: null,
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0xcCc8CC82868B94Bc2759c69375fC7Ae769703EB8",
	fromTimestamp: "0",
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0x9fa01a45e245015fa685f21763e60c60832ed2d6",
	mainColor: solverColors.get(SolverName.RASA),
}

export const zenith1_solver: Solver = {
	name: SolverName.ZENITH,
	address: "0x6d1d09586a274517c5a089364a93c02b6b261990",
	mainColor: solverColors.get(SolverName.ZENITH),
}

export const zenith2_solver: Solver = {
	name: SolverName.ZENITH,
	address: "0xd5e4b5928d99e7afbea497a301ca5fa2e752b101",
	mainColor: solverColors.get(SolverName.ZENITH),
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xd5a075c88a4188d666fa1e4051913be6782982da",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps2_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xdf077f5f52bc41a9072f9d0e5fb281770bcd1142",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xdfed11fe4af63b059edbbdf53e9c633b331ed432",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "BNB",
	serverUrl: "https://analytics-api.symm.io",
	assetsFolder: "thena",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/bnb_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x55d398326f99059ff775485246999027b3197955"],
	version: Version.LATEST,
	startDate: new Date(1702058147000),
	affiliates: [alpha_v3, cloverfield],
	solvers: [rasa_solver, perps1_solver, perps2_solver, perps3_solver, zenith1_solver, zenith2_solver],
}
