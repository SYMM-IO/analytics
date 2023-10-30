import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";

export const subEnvironment: SubEnvironmentInterface = {
	name: "Based",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_base_8",
	collateralDecimal: 6,
	mainColor: "#F5B3F7",
	accountSource: "0x5dE6949717F3AA8E0Fbed5Ce8B611Ebcf1e44AE9",
	fromTimestamp: "0",
}

export const environment: EnvironmentInterface = {
	assetsFolder: "based",
	environments: [
		subEnvironment
	]
}

