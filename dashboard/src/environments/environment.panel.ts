import {EnvironmentInterface} from "./environment-interface"
import {environment as bnb82Env} from "./environment.bnb_8_2"
import {environment as base82Env} from "./environment.base_8_2"
import {environment as blast82Env} from "./environment.blast_8_2"

export const environment: EnvironmentInterface = {
    name: "panel",
    assetsFolder: "panel",
    serverUrl: "https://analytics-api.symm.io",
    panel: true,
    environments: [
        // ftmEnv,
        // bnbEnv,
        // baseEnv,
        bnb82Env,
        blast82Env,
        base82Env,
    ],
}