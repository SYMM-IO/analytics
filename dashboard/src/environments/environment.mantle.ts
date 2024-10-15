import { Affiliate, affiliateColors, AffiliateName, EnvironmentInterface, Solver, solverColors, SolverName, Version } from "./environment-interface"

export const intentX: Affiliate = {
	name: AffiliateName.INTENTX,
	mainColor: affiliateColors.get(AffiliateName.INTENTX),
	address: "0xECbd0788bB5a72f9dFDAc1FFeAAF9B7c2B26E456",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0xfA8A07fcB6204Ce2229C244a26F42563A72f369E",
	fromTimestamp: "0",
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0x50e88c692b137b8a51b6017026ef414651e0d5ba",
	mainColor: solverColors.get(SolverName.RASA),
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x12de0352dd4187af5797f5147c4179f9624346e2",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps2_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x614bb1f3e0ae5a393979468ed89088f05277312c",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xf9e39b4b30e26c18d2a725c0397ed5a925efe46b",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "MANTLE",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/mantle_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x5d3a1Ff2b6BAb83b63cd9AD0787074081a52ef34"],
	version: Version.LATEST,
	startDate: new Date(1712075812000),
	affiliates: [intentX, cloverfield],
	solvers: [rasa_solver, perps1_solver, perps2_solver, perps3_solver],
}
