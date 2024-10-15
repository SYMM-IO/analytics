import { Affiliate, affiliateColors, AffiliateName, EnvironmentInterface, Solver, solverColors, SolverName, Version } from "./environment-interface"
import BigNumber from "bignumber.js"

export const based: Affiliate = {
	name: AffiliateName.BASED,
	mainColor: affiliateColors.get(AffiliateName.BASED),
	address: "0x5de6949717f3aa8e0fbed5ce8b611ebcf1e44ae9",
	fromTimestamp: "1692265765",
	depositDiff: BigNumber("1289164045865600000000"),
}

export const intentx: Affiliate = {
	name: AffiliateName.INTENTX,
	mainColor: affiliateColors.get(AffiliateName.INTENTX),
	address: "0x724796d2e9143920b1b58651b04e1ed201b8cc98",
	fromTimestamp: "0",
}

export const solver: Solver = {
	name: SolverName.RASA,
	address: "0xed85c23e307e0f40cc38d6aa42fe25e0a5d07ea7",
	mainColor: solverColors.get(SolverName.RASA),
}

export const environment: EnvironmentInterface = {
	name: "BASE_8",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/base_0_8_0_analytics/latest/gn",
	version: Version.V_0_8_0,
	collateralDecimal: 6,
	collaterals: ["0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA"],
	affiliates: [based, intentx],
	solvers: [solver],
}
