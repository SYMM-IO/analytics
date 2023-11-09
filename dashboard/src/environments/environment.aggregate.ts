import {EnvironmentInterface} from "./environment-interface"

import {subEnvironment as thenaEnvV1} from "./environment.alpha_thena_v1"
import {subEnvironment as thenaEnvV2} from "./environment.alpha_thena_v2"
import {subEnvironment as basedEnv} from "./environment.based"
import {subEnvironment as cloverfieldBnbEnv} from "./environment.cloverfield_bsc"
import {subEnvironment as cloverfieldFantomEnv} from "./environment.cloverfield_fantom"
import {subEnvironment as intentXEnv} from "./environment.intentx"

export const environment: EnvironmentInterface = {
	assetsFolder: "aggregate",
	aggregate: true,
	environments: [
		intentXEnv,
		thenaEnvV1,
		thenaEnvV2,
		basedEnv,
		cloverfieldBnbEnv,
		cloverfieldFantomEnv
	]
}