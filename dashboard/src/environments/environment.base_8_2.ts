import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"


export const based: Affiliate = {
    name: "Based",
    mainColor: "#F5B3F7",
    accountSource: "0x1c03B6480a4efC2d4123ba90d7857f0e1878B780",
    fromTimestamp: "0",
}

export const intentx: Affiliate = {
    name: "IntentX",
    mainColor: "#F20C27",
    accountSource: "0x8Ab178C07184ffD44F0ADfF4eA2ce6cFc33F3b86",
    fromTimestamp: "0",
}

export const hedger: Hedger = {
    name: "Based_IntentX_Hedger",
}


export const environment: EnvironmentInterface = {
    name: "BASE_8_2",
    serverUrl: "https://analytics-api.symm.io",
    subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_base_8_2",
    collateralDecimal: 6,
    startDate: new Date(1702466963000),
    affiliates: [
        based,
        intentx,
    ],
    hedgers: [
        hedger,
    ],
}

