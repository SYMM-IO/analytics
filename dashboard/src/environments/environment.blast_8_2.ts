import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const core: Affiliate = {
    name: "Core",
    mainColor: "#D4E09B",
    accountSource: "0xd6ee1fd75d11989e57B57AA6Fd75f558fBf02a5e",
    fromTimestamp: "0",
}

export const hedger: Hedger = {
    name: "Core_Hedger",
}


export const environment: EnvironmentInterface = {
    name: "BLAST_8_2",
    serverUrl: "https://analytics-api.symm.io",
    subgraphUrl: "https://api.studio.thegraph.com/query/62454/analytics_blast_8_2/version/latest",
    collateralDecimal: 18,
    startDate: new Date(1709897970000),
    affiliates: [
        core,
    ],
    hedgers: [
        hedger,
    ],
}

