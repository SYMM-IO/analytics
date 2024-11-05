import {EnvironmentInterface} from "./environment-interface"
import {environment as bnb82Env} from "./environment.bnb"
import {environment as base82Env} from "./environment.base"
import {environment as blast82Env} from "./environment.blast"

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