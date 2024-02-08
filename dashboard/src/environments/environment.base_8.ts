import {Affiliate, EnvironmentInterface, Hedger} from "./environment-interface"
import BigNumber from "bignumber.js"

export const based: Affiliate = {
    name: "Based",
    mainColor: "#F5B3F7",
    accountSource: "0x5de6949717f3aa8e0fbed5ce8b611ebcf1e44ae9",
    fromTimestamp: "1692265765",
    depositDiff: BigNumber("1289164045865600000000"),
}

export const intentx: Affiliate = {
    name: "IntentX",
    mainColor: "#F20C27",
    accountSource: "0x724796d2e9143920b1b58651b04e1ed201b8cc98",
    fromTimestamp: "0",
}

export const hedger: Hedger = {
    name: "Based_IntentX_Hedger",
}

export const environment: EnvironmentInterface = {
    name: "BASE_8",
    serverUrl: "http://analytics-api.symm.io",
    subgraphUrl: "https://api.thegraph.com/subgraphs/name/symmiograph/symmioanalytics_base_8",
    collateralDecimal: 6,
    affiliates: [
        based,
        intentx,
    ],
    hedgers: [
        hedger,
    ],
}

