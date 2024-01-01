import {EnvironmentInterface} from "./environment-interface"
import {environment as base8Env} from "./environment.base_8"

export const environment: EnvironmentInterface = {
    name: "Based",
    assetsFolder: "based",
    singleAffiliateAccountSource: "0x5de6949717f3aa8e0fbed5ce8b611ebcf1e44ae9",
    environments: [
        base8Env,
    ],
}