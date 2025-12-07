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

export const bmx: Affiliate = {
	name: AffiliateName.BMX,
	mainColor: affiliateColors.get(AffiliateName.BMX),
	address: "0xC0ff4B56f62f20bA45f4229CC6BAaD986FA2a904",
	fromTimestamp: null,
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0x3adc81CC43d9e1636de9cbac764Afcb1F3ae6cde",
	fromTimestamp: "0",
}

export const xpanse: Affiliate = {
	name: AffiliateName.XPANSE,
	mainColor: affiliateColors.get(AffiliateName.XPANSE),
	address: "0xDE6446197Cd1AE02E1C5B7191a626Fb0c1757377",
	fromTimestamp: "0",
}

export const perps1_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x78e76ac7fec050ca785c19ffaddf57137b890543",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps2_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x7d387771f6e23f353a4afce21af521875c0825d0",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x87fc464fa528260f1eeab94fa20f73fed8536eb7",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const environment: EnvironmentInterface = {
	name: "Mode",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/mode_analytics/latest/gn",
	collateralDecimal: 18,
	collaterals: ["0xd988097fb8612cc24eeC14542bC03424c656005f"],
	version: Version.LATEST,
	startDate: new Date(1722690000000),
	affiliates: [bmx, cloverfield, xpanse, NULL_AFFILIATE],
	solvers: [perps1_solver, perps2_solver, perps3_solver],
}
