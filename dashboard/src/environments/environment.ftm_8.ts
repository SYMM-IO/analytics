import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"

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
    subgraphUrl: "https://api.studio.thegraph.com/query/62454/symmioanalytics_ftm_8/version/latest",
    collateralDecimal: 6,
    affiliates: [
        cloverfield,
    ],
    hedgers: [
        hedger,
    ],
}
