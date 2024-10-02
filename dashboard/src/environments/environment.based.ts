import {EnvironmentInterface, Version} from "./environment-interface"
import {environment as base82Env} from "./environment.base_8_2"

export const environment: EnvironmentInterface = {
    name: "Based",
    assetsFolder: "based",
    version: Version.V_0_8_2,
    singleAffiliateAccountSource: "0x1c03B6480a4efC2d4123ba90d7857f0e1878B780",
    environments: [
        base82Env,
    ],
}