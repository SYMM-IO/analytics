import BigNumber from "bignumber.js"

export interface EnvironmentInterface {
    name: string;
    assetsFolder?: string;
    panel?: boolean;
    serverUrl?: string;
    subgraphUrl?: string;
    collateralDecimal?: number;
    startDate?: Date;
    singleAffiliateAccountSource?: string;
    affiliates?: Affiliate[];
    hedgers?: Hedger[];
    environments?: EnvironmentInterface[];
}

export interface Affiliate {
    name?: string;
    mainColor?: string;
    accountSource?: string;
    fromTimestamp: string | null;
    depositDiff?: BigNumber;
}

export interface Hedger {
    name?: string;
}