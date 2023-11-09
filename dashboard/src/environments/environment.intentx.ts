import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";

export const subEnvironment: SubEnvironmentInterface = {
	name: "IntentX",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_base_8",
	collateralDecimal: 6,
	mainColor: "#F20C27",
	accountSource: "0x724796d2e9143920B1b58651B04e1Ed201b8cC98",
	fromTimestamp: "0",
}

export const environment: EnvironmentInterface = {
	assetsFolder: "intentX",
	environments: [
		subEnvironment
	]
}

