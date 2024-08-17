import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"


export const core: Affiliate = {
	name: "Core",
	mainColor: "#C8C903",
	accountSource: "0xd6ee1fd75d11989e57B57AA6Fd75f558fBf02a5e",
	fromTimestamp: "0",
}

export const intentX: Affiliate = {
	name: "IntentX",
	mainColor: "#F20C27",
	accountSource: "0x083267D20Dbe6C2b0A83Bd0E601dC2299eD99015",
	fromTimestamp: "0",
}

export const cloverfield: Affiliate = {
	name: "Cloverfield",
	mainColor: "#A2D4EA",
	accountSource: "0xE59D420c979Cd433DD1F2673991667D4DeAf01ae",
	fromTimestamp: "0",
}

export const hedger: Hedger = {
	name: "Blast_Hedger",
}

export const environment: EnvironmentInterface = {
	name: "BLAST_8_2",
	serverUrl: "https://analytics-api.symm.io",
	subgraphUrl: "https://api.studio.thegraph.com/query/62454/analytics_blast_8_2/version/latest",
	collateralDecimal: 18,
	version: Version.V_0_8_2,
	startDate: new Date(1709897970000),
	affiliates: [
		core,
		intentX,
		cloverfield
	],
	hedgers: [
		hedger,
	],
}

