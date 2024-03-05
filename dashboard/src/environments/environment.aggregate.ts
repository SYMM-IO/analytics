import {EnvironmentInterface} from "./environment-interface"

import {environment as bnbEnv} from "./environment.bnb_8"
import {environment as bnb82Env} from "./environment.bnb_8_2"
import {environment as base82Env} from "./environment.base_8_2"
import {environment as ftmEnv} from "./environment.ftm_8"
import {environment as baseEnv} from "./environment.base_8"
import {environment as blast82Env} from "./environment.blast_8_2"

export const environment: EnvironmentInterface = {
    name: "aggregate",
    assetsFolder: "aggregate",
    serverUrl: "https://analytics-api.symm.io",
    environments: [
        ftmEnv,
        bnbEnv,
        bnb82Env,
        baseEnv,
        base82Env,
        blast82Env,
    ],
}