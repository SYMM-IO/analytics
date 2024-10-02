import {EnvironmentInterface} from "./environment-interface"
import {environment as bnb82Env} from "./environment.bnb_8_2"

export const environment: EnvironmentInterface = {
    name: "Alpha Thena",
    assetsFolder: "thena",
    singleAffiliateAccountSource: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
    environments: [
        bnb82Env,
    ],
}