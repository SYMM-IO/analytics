import { Affiliate, affiliateColors, AffiliateName, EnvironmentInterface, Solver, solverColors, SolverName, Version } from "./environment-interface"

export const based: Affiliate = {
	name: AffiliateName.BASED,
	mainColor: affiliateColors.get(AffiliateName.BASED),
	address: "0x1c03B6480a4efC2d4123ba90d7857f0e1878B780",
	fromTimestamp: "0",
}

export const intentx: Affiliate = {
	name: AffiliateName.INTENTX,
	mainColor: affiliateColors.get(AffiliateName.INTENTX),
	address: "0x8Ab178C07184ffD44F0ADfF4eA2ce6cFc33F3b86",
	fromTimestamp: "0",
}

export const bmx: Affiliate = {
	name: AffiliateName.BMX,
	mainColor: affiliateColors.get(AffiliateName.BMX),
	address: "0x6d63921d8203044f6abad8f346d3aea9a2719ddd",
	fromTimestamp: "0",
}

export const beFi: Affiliate = {
	name: AffiliateName.BEFI,
	mainColor: affiliateColors.get(AffiliateName.BEFI),
	address: "0xc6Ecf3AB3D09ba6f1565Ad6E139B5D3ba30bB774",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: AffiliateName.CLOVERFIELD,
	mainColor: affiliateColors.get(AffiliateName.CLOVERFIELD),
	address: "0xf7f56d7e02d5c7bf33525ae2eecb049a17ef4580",
	fromTimestamp: "0",
}

export const privex: Affiliate = {
	name: AffiliateName.PRIVEX,
	mainColor: affiliateColors.get(AffiliateName.PRIVEX),
	address: "0x921Dd892D67Aed3d492F9ad77b30b60160B53Fe1",
	fromTimestamp: "0",
}

export const rasa_solver: Solver = {
	name: SolverName.RASA,
	address: "0x9206d9d8f7f1b212a4183827d20de32af3a23c59",
	mainColor: solverColors.get(SolverName.RASA),
}

export const perps_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x12de0352dd4187af5797f5147c4179f9624346e2",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const zenith_solver: Solver = {
	name: SolverName.ZENITH,
	address: "0x5f3525db7589640dae87d6040a85c49fa43feb2f",
	mainColor: solverColors.get(SolverName.ZENITH),
}

export const zenith2_solver: Solver = {
	name: SolverName.ZENITH,
	address: "0x94D2c48821F7667923d7656ACc3529b953b40D09",
	mainColor: solverColors.get(SolverName.ZENITH),
}

export const environment: EnvironmentInterface = {
	name: "BASE",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/base_analytics/latest/gn",
	collateralDecimal: 6,
	collaterals: ["0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"],
	version: Version.LATEST,
	startDate: new Date(1702466963000),
	affiliates: [based, intentx, bmx, beFi, privex, cloverfield],
	solvers: [rasa_solver, perps_solver, zenith_solver, zenith2_solver],
}
