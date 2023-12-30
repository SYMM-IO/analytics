import {EnvironmentInterface} from "./environment-interface"
import {environment as bnbEnv} from "./environment.bnb_8"

export const environment: EnvironmentInterface = {
    name: "Legacy Alpha Thena",
    assetsFolder: "thena",
    singleAffiliateAccountSource: "0x75c539eFB5300234e5DaA684502735Fc3886e8b4",
    environments: [
        bnbEnv,
    ],
}