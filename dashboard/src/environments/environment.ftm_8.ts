import { Affiliate, affiliateColors, AffiliateName, EnvironmentInterface, Solver, solverColors, SolverName, Version } from "./environment-interface"

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0x0937bC09b8D073E4F1abE85470969475f714Ca6c",
	fromTimestamp: null,
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0x3ea3400d474b73941dda97d182a8aa80165f952e",
	mainColor: solverColors.get(SolverName.RASA),
}

export const environment: EnvironmentInterface = {
	name: "FTM_8",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/fantom_0_8_0_analytics/latest/gn",
	collateralDecimal: 6,
	collaterals: ["0x28a92dde19d9989f39a49905d7c9c2fac7799bdf", "0x049d68029688eAbF473097a2fC38ef61633A3C7A"],
	version: Version.V_0_8_0,
	affiliates: [cloverfield],
	solvers: [rasa_solver],
}
