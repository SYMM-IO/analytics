import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"

export const cloverfield: Affiliate = {
    name: "Cloverfield Fantom",
    mainColor: "#0eb1fc",
    accountSource: "0x0937bC09b8D073E4F1abE85470969475f714Ca6c",
    fromTimestamp: null,
}

export const hedger: Hedger = {
    name: "Cloverfield_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "FTM_8",
    serverUrl: "https://api.analytics.symm.io",
    subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_ftm_8",
    collateralDecimal: 6,
    affiliates: [
        cloverfield,
    ],
    hedgers: [
        hedger,
    ],
}
