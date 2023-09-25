import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";

export const subEnvironment: SubEnvironmentInterface = {
	name: "Based",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/navid-fkh/symmetrical_base",
	collateralDecimal: 6,
	mainColor: "#F5B3F7",
	accountSource: "0x5dE6949717F3AA8E0Fbed5Ce8B611Ebcf1e44AE9",
	fromTimestamp: "1692541495",
}

export const environment: EnvironmentInterface = {
	assetsFolder: "based",
	environments: [
		subEnvironment
	]
}

