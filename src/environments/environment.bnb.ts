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

export const alpha_v3_1: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
	fromTimestamp: null,
}

export const alpha_v3_2: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0xdAA571297038eeCB31dCafc3d1ff2C1A138E41C9",
	fromTimestamp: null,
}

export const alpha_v3_3: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0xf3d56c3c1E610581181f4dE9242DbDa92D583dD6",
	fromTimestamp: null,
}

export const alpha_v3_4: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x49f49005e8e4D333459a05CCD34D00EB30D67446",
	fromTimestamp: null,
}

export const alpha_v3_5: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x2035CAC2C606c66e0B650f6E102bfAF931218432",
	fromTimestamp: null,
}

export const alpha_v3_6: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0xBCc250B8D7e7e378c85fe9bc83fF0Eff5d5b0f20",
	fromTimestamp: null,
}

export const alpha_v3_7: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x7634Fd3084286e15DE973eca9a56dD353dAB3eE3",
	fromTimestamp: null,
}

export const alpha_v3_8: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0xeFD638A013bF62638EfB4a405aca804F5f7d6cb8",
	fromTimestamp: null,
}

export const alpha_v3_9: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x041e372ed328a6088e470476e6df92617a86e2b2",
	fromTimestamp: null,
}

export const alpha_v3_10: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x4986415e243b9db258124909facb0a6aa87f6ccd",
	fromTimestamp: null,
}

export const alpha_v3_11: Affiliate = {
	name: AffiliateName.THENA,
	mainColor: affiliateColors.get(AffiliateName.THENA),
	address: "0x723abb2ef943d816a010f6f2ed510e513cc0d7f3",
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
	subgraphUrl: "https://api.goldsky.com/api/public/project_cmi1t9ac85xtt01zf0gpn0sw1/subgraphs/bnb_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x55d398326f99059ff775485246999027b3197955"],
	version: Version.LATEST,
	startDate: new Date(1702058147000),
	affiliates: [alpha_v3_1, alpha_v3_2, alpha_v3_3, alpha_v3_4, alpha_v3_5, alpha_v3_6, alpha_v3_7, alpha_v3_8, cloverfield, NULL_AFFILIATE],
	solvers: [rasa_solver, perps1_solver, perps2_solver, perps3_solver, zenith1_solver, zenith2_solver],
}
