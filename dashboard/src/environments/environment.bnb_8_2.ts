import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const alpha_v3: Affiliate = {
    name: "Alpha Thena",
    mainColor: "#ED00C9",
    accountSource: "0x650a2D6C263A93cFF5EdD41f836ce832F05A1cF3",
    fromTimestamp: null,
}

export const hedger: Hedger = {
    name: "Thena_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "BNB_8_2",
    serverUrl: "https://api.analytics.symm.io",
    assetsFolder: "thena",
    subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_bnb_8_2",
    collateralDecimal: 18,
    affiliates: [
        alpha_v3,
    ],
    hedgers: [
        hedger,
    ],
}

