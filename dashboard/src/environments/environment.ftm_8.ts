import {Affiliate, EnvironmentInterface, Hedger, Version} from "./environment-interface"

export const cloverfield: Affiliate = {
    name: "Cloverfield",
    mainColor: "#A2D4EA",
    accountSource: "0x0937bC09b8D073E4F1abE85470969475f714Ca6c",
    fromTimestamp: null,
}

export const hedger: Hedger = {
    name: "Cloverfield_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "FTM_8",
    serverUrl: "https://analytics-api.symm.io",
    subgraphUrl: "https://api.goldsky.com/api/public/project_cm1hfr4527p0f01u85mz499u8/subgraphs/fantom_0_8_0_analytics/latest/gn",
    collateralDecimal: 6,
    version: Version.V_0_8_0,
    affiliates: [
        cloverfield,
    ],
    hedgers: [
        hedger,
    ],
}
