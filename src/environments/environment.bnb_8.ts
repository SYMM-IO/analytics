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

export const alpha_v1: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x058Ba7574d8bC66F1a1DCc44bb5B18894D4190e0",
	fromTimestamp: null,
}

export const alpha_v2: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x75c539eFB5300234e5DaA684502735Fc3886e8b4",
	fromTimestamp: null,
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0x10acc15db0d432280be4885dae65e1cc76da3c54",
	fromTimestamp: null,
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0x62ad8de6740314677f06723a7a07797ae5082dbb",
	mainColor: solverColors.get(SolverName.RASA),
}

export const environment: EnvironmentInterface = {
	name: "BNB_8",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/bnb_0_8_0_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x55d398326f99059ff775485246999027b3197955"],
	version: Version.V_0_8_0,
	affiliates: [cloverfield, alpha_v1, alpha_v2, NULL_AFFILIATE],
	solvers: [rasa_solver],
}
