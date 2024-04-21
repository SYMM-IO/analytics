import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const intentX: Affiliate = {
    name: "IntentX",
    mainColor: "#F20C27",
    accountSource: "0xECbd0788bB5a72f9dFDAc1FFeAAF9B7c2B26E456",
    fromTimestamp: "0",
}

export const hedger: Hedger = {
    name: "Mantle_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "MANTLE_8_2",
    serverUrl: "https://analytics-api.symm.io",
    subgraphUrl: "https://subgraph-api.mantle.xyz/subgraphs/name/analytics_mantle_8_2",
    collateralDecimal: 18,
    startDate: new Date(1712075812000),
    affiliates: [
        intentX
    ],
    hedgers: [
        hedger,
    ],
}

