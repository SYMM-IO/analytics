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

export const core: Affiliate = {
	name: AffiliateName.CORE,
	mainColor: affiliateColors.get(AffiliateName.CORE),
	address: "0xd6ee1fd75d11989e57B57AA6Fd75f558fBf02a5e",
	fromTimestamp: "0",
}

export const intentX: Affiliate = {
	name: AffiliateName.INTENTX,
	mainColor: affiliateColors.get(AffiliateName.INTENTX),
	address: "0x083267D20Dbe6C2b0A83Bd0E601dC2299eD99015",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0xE59D420c979Cd433DD1F2673991667D4DeAf01ae",
	fromTimestamp: "0",
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0xecbd0788bb5a72f9dfdac1ffeaaf9b7c2b26e456",
	mainColor: solverColors.get(SolverName.RASA),
}

export const environment: EnvironmentInterface = {
	name: "BLAST",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cmi1t9ac85xtt01zf0gpn0sw1/subgraphs/blast_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0x4300000000000000000000000000000000000003"],
	version: Version.LATEST,
	startDate: new Date(1709897970000),
	affiliates: [core, intentX, cloverfield, NULL_AFFILIATE],
	solvers: [rasa_solver],
}
