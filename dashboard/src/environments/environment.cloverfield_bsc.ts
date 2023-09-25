import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";

export const subEnvironment: SubEnvironmentInterface = {
	name: "Cloverfield BNB",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/navid-fkh/symmetrical_bsc",
	collateralDecimal: 18,
	mainColor: "#A2D4EA",
	accountSource: "0x10acc15db0d432280be4885dae65e1cc76da3c54",
	fromTimestamp: null,
}

export const environment: EnvironmentInterface = {
	assetsFolder: "cloverfield",
	environments: [
		subEnvironment
	]
}
