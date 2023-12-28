import {EnvironmentInterface} from "./environment-interface"
import {environment as bnb82Env} from "./environment.bnb_8_2"

export const environment: EnvironmentInterface = {
    name: "Alpha Thena",
    assetsFolder: "thena",
    singleAffiliateName: "Alpha Thena V3",
    environments: [
        bnb82Env,
    ],
}