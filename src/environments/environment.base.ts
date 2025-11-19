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

export const xpanse: Affiliate = {
	name: AffiliateName.XPANSE,
	mainColor: affiliateColors.get(AffiliateName.XPANSE),
	address: "0xDE6446197Cd1AE02E1C5B7191a626Fb0c1757377",
	fromTimestamp: "0",
}

export const vibe: Affiliate = {
	name: AffiliateName.VIBE,
	mainColor: affiliateColors.get(AffiliateName.VIBE),
	address: "0x95605c64356572eb5C076Cb9c027c88b527A2059".toLowerCase(),
	fromTimestamp: "0",
}

export const carbon: Affiliate = {
	name: AffiliateName.CARBON,
	mainColor: affiliateColors.get(AffiliateName.CARBON),
	address: "0x39EcC772f6073242d6FD1646d81FA2D87fe95314".toLowerCase(),
	fromTimestamp: "0",
}

export const pear: Affiliate = {
	name: AffiliateName.PEAR,
	mainColor: affiliateColors.get(AffiliateName.PEAR),
	address: "0xE43166cE17d3511B09438a359dAa53513225101D".toLowerCase(),
	fromTimestamp: "0",
}

export const quickswap: Affiliate = {
	name: AffiliateName.QUICKSWAP,
	mainColor: affiliateColors.get(AffiliateName.QUICKSWAP),
	address: "0x0B4779a37C5E6cD7060cc265105Ff44a03b47b26".toLowerCase(),
	fromTimestamp: "0",
}

export const treble: Affiliate = {
	name: AffiliateName.TREBLE,
	mainColor: affiliateColors.get(AffiliateName.TREBLE),
	address: "0x72b03E85B40A745B07f3a15e7A02E66F7f8352F3".toLowerCase(),
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

export const perps2_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0x1ecabf0eba136920677c9575faccee36f30592cf",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}

export const perps3_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xfc4ac3af357ebe6d556dcd72453e9b30f6dc6873",
	mainColor: solverColors.get(SolverName.PERPS_HUB),
}
export const perps4_solver: Solver = {
	name: SolverName.PERPS_HUB,
	address: "0xB6e3b44975f2966707a91747F89D2002ff8d62Db",
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

export const carbon_solver: Solver = {
	name: SolverName.CARBON,
	address: "0x9F20BaD77CCa97f2F96De88b146603Ca3F65baD5",
	mainColor: solverColors.get(SolverName.CARBON),
}

export const carbon2_solver: Solver = {
	name: SolverName.CARBON,
	address: "0xB49Cae38c96f6425Ce4A46e8220549C6a13362bE",
	mainColor: solverColors.get(SolverName.CARBON),
}

export const environment: EnvironmentInterface = {
	name: "BASE",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.studio.thegraph.com/query/85206/base-analytics/version/latest",
	collateralDecimal: 6,
	collaterals: ["0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"],
	version: Version.LATEST,
	startDate: new Date(1702466963000),
	affiliates: [based, intentx, bmx, beFi, privex, cloverfield, xpanse, vibe, carbon, pear, quickswap, treble, NULL_AFFILIATE],
	solvers: [rasa_solver, perps_solver, perps2_solver, perps3_solver, perps4_solver, zenith_solver, zenith2_solver, carbon_solver, carbon2_solver],
}
