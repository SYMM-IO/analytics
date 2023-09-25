import {EnvironmentInterface, SubEnvironmentInterface} from "./environment-interface";

export const subEnvironment: SubEnvironmentInterface = {
	name: "Cloverfield Fantom",
	subgraphUrl: "https://api.thegraph.com/subgraphs/name/navid-fkh/symmetrical_fantom",
	collateralDecimal: 6,
	mainColor: "#A2D4EA",
	accountSource: "0x0937bC09b8D073E4F1abE85470969475f714Ca6c",
	fromTimestamp: null,
}

export const environment: EnvironmentInterface = {
	assetsFolder: "cloverfield",
	environments: [
		subEnvironment
	]
}
