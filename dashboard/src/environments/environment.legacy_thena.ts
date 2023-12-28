import {EnvironmentInterface} from "./environment-interface"
import {environment as bnbEnv} from "./environment.bnb_8"

export const environment: EnvironmentInterface = {
    name: "Legacy Alpha Thena",
    assetsFolder: "thena",
    singleAffiliateName: "Alpha Thena V2",
    environments: [
        bnbEnv,
    ],
}