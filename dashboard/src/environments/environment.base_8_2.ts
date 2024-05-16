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

export const morphex: Affiliate = {
    name: "Morphex",
    mainColor: "#1F61B5",
    accountSource: "0x6D63921D8203044f6AbaD8F346d3AEa9A2719dDD",
    fromTimestamp: "0",
}

export const beFi: Affiliate = {
    name: "BeFi",
    mainColor: "#FE9E0F",
    accountSource: "0xc6Ecf3AB3D09ba6f1565Ad6E139B5D3ba30bB774",
    fromTimestamp: "0",
}

export const hedger: Hedger = {
    name: "Based_IntentX_Hedger",
}


export const environment: EnvironmentInterface = {
    name: "BASE_8_2",
    serverUrl: "https://analytics-api.symm.io",
    subgraphUrl: "https://api.studio.thegraph.com/query/62454/analytics_base_8_2/version/latest",
    collateralDecimal: 6,
    startDate: new Date(1702466963000),
    affiliates: [
        based,
        intentx,
        morphex,
        beFi
    ],
    hedgers: [
        hedger,
    ],
}

