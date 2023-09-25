import {EnvironmentInterface} from "./environment-interface";

import {subEnvironment as thenaEnv} from "./environment.alpha_thena"
import {subEnvironment as basedEnv} from "./environment.based"
import {subEnvironment as cloverfieldBnbEnv} from "./environment.cloverfield_bsc"
import {subEnvironment as cloverfieldFantomEnv} from "./environment.cloverfield_fantom"

export const environment: EnvironmentInterface = {
	assetsFolder: "aggregate",
	aggregate: true,
	environments: [
		thenaEnv,
		basedEnv,
		cloverfieldBnbEnv,
		cloverfieldFantomEnv
	]
};