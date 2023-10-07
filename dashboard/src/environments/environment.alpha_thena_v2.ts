import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";


export const subEnvironment: SubEnvironmentInterface = {
	name: "Alpha Thena V2",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_bnb_8",
	collateralDecimal: 18,
	mainColor: "#ED00C9",
	accountSource: "0x75c539eFB5300234e5DaA684502735Fc3886e8b4",
	fromTimestamp: null,
}

export const environment: EnvironmentInterface = {
	assetsFolder: "thena",
	environments: [
		subEnvironment
	]
}

