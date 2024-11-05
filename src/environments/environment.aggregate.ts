import { EnvironmentInterface } from "./environment-interface"

import { environment as bnb8Env } from "./environment.bnb_8"
import { environment as bnbEnv } from "./environment.bnb"
import { environment as base8Env } from "./environment.base_8"
import { environment as baseEnv } from "./environment.base"
import { environment as ftm8Env } from "./environment.ftm_8"
import { environment as blastEnv } from "./environment.blast"
import { environment as mantleEnv } from "./environment.mantle"
import { environment as arbitrumEnv } from "./environment.arbitrum"
import { environment as modeEnv } from "./environment.mode"

export const environment: EnvironmentInterface = {
	name: "aggregate",
	assetsFolder: "aggregate",
	serverUrl: "https://analytics-api.symm.io",
	environments: [ftm8Env, bnb8Env, bnbEnv, base8Env, baseEnv, blastEnv, mantleEnv, arbitrumEnv, modeEnv],
}
