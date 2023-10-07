import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";


export const subEnvironment: SubEnvironmentInterface = {
	name: "Alpha Thena V1",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_bnb_8",
	collateralDecimal: 18,
	mainColor: "#8a377c",
	accountSource: "0x058Ba7574d8bC66F1a1DCc44bb5B18894D4190e0",
	fromTimestamp: null,
}

export const environment: EnvironmentInterface = {
	assetsFolder: "thena",
	environments: [
		subEnvironment
	]
}

