import {EnvironmentInterface} from "./environment-interface"

import {environment as bnbEnv} from "./environment.bnb_8"
import {environment as bnb82Env} from "./environment.bnb_8_2"
import {environment as ftmEnv} from "./environment.ftm_8"
import {environment as baseEnv} from "./environment.base_8"

export const environment: EnvironmentInterface = {
    name: "aggregate",
    assetsFolder: "aggregate",
    serverUrl: "https://api.analytics.symm.io",
    environments: [
        ftmEnv,
        bnbEnv,
        bnb82Env,
        baseEnv,
    ],
}