import { EnvironmentInterface } from "./environment-interface"

import { environment as bnbEnv } from "./environment.bnb"
import { environment as baseEnv } from "./environment.base"
import { environment as ftm8Env } from "./environment.ftm_8"
import { environment as blastEnv } from "./environment.blast"
import { environment as mantleEnv } from "./environment.mantle"
import { environment as arbitrumEnv } from "./environment.arbitrum"
import { environment as beraEnv } from "./environment.bera"
import { environment as sonicEnv } from "./environment.sonic"
import { environment as cotiEnv } from "./environment.coti"

export const environment: EnvironmentInterface = {
	name: "aggregate",
	assetsFolder: "aggregate",
	serverUrl: "https://analytics-api.symm.io",
	environments: [ftm8Env, bnbEnv, baseEnv, blastEnv, mantleEnv, arbitrumEnv, beraEnv, sonicEnv, cotiEnv],
}
