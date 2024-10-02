import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"


export const based: Affiliate = {
	name: "Based",
	mainColor: "#F5B3F7",
	accountSource: "0x1c03B6480a4efC2d4123ba90d7857f0e1878B780",
	fromTimestamp: "0",
}

export const intentx: Affiliate = {
	name: "IntentX",
	mainColor: "#F20C27",
	accountSource: "0x8Ab178C07184ffD44F0ADfF4eA2ce6cFc33F3b86",
	fromTimestamp: "0",
}

export const mbx: Affiliate = {
	name: "BMX",
	mainColor: "#1F61B5",
	accountSource: "0x6D63921D8203044f6AbaD8F346d3AEa9A2719dDD",
	fromTimestamp: "0",
}

export const beFi: Affiliate = {
	name: "BeFi",
	mainColor: "#FE9E0F",
	accountSource: "0xc6Ecf3AB3D09ba6f1565Ad6E139B5D3ba30bB774",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: "Cloverfield",
	mainColor: "#A2D4EA",
	accountSource: "0xF7F56d7E02D5c7bF33525AE2eecB049a17Ef4580",
	fromTimestamp: "0",
}

export const hedger: Hedger = {
	name: "Based_IntentX_Hedger",
}


export const environment: EnvironmentInterface = {
	name: "BASE_8_2",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/base_analytics/latest/gn",
	collateralDecimal: 6,
	version: Version.V_0_8_2,
	startDate: new Date(1702466963000),
	affiliates: [
		based,
		intentx,
		mbx,
		beFi,
		cloverfield
	],
	hedgers: [
		hedger,
	],
}

