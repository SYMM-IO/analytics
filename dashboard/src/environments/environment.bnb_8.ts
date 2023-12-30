import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const alpha_v1: Affiliate = {
    name: "Alpha Thena",
    mainColor: "#ED00C9",
    accountSource: "0x058Ba7574d8bC66F1a1DCc44bb5B18894D4190e0",
    fromTimestamp: null,
}

export const alpha_v2: Affiliate = {
    name: "Alpha Thena",
    mainColor: "#ED00C9",
    accountSource: "0x75c539eFB5300234e5DaA684502735Fc3886e8b4",
    fromTimestamp: null,
}

export const cloverfield: Affiliate = {
    name: "Cloverfield",
    mainColor: "#A2D4EA",
    accountSource: "0x10acc15db0d432280be4885dae65e1cc76da3c54",
    fromTimestamp: null,
}

export const hedger: Hedger = {
    name: "Thena_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "BNB_8",
    serverUrl: "https://api.analytics.symm.io",
    subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_bnb_8",
    collateralDecimal: 18,
    affiliates: [
        cloverfield,
        alpha_v1,
        alpha_v2,
    ],
    hedgers: [
        hedger,
    ],
}

