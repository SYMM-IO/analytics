import BigNumber from "bignumber.js";

export class User {
    id?: string;
    timestamp?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): User {
        const user = new User();
        user.id = raw.id;
        user.timestamp = new BigNumber(raw.timestamp);
        user.transaction = raw.transaction;
        return user;
    }
}

export class Account {
    id?: string;
    user?: string;
    timestamp?: BigNumber;
    name?: string;
    quotesCount?: BigNumber;
    positionsCount?: BigNumber;
    lastActivityTimestamp?: BigNumber;
    deposit?: BigNumber;
    withdraw?: BigNumber;
    allocated?: BigNumber;
    deallocated?: BigNumber;
    transaction?: string;
    accountSource?: string;

    static fromRawObject(raw: any): Account {
        const account = new Account();
        account.id = raw.id;
        account.user = raw.user;
        account.timestamp = new BigNumber(raw.timestamp);
        account.name = raw.name;
        account.quotesCount = new BigNumber(raw.quotesCount);
        account.positionsCount = new BigNumber(raw.positionsCount);
        account.lastActivityTimestamp = new BigNumber(raw.lastActivityTimestamp);
        account.deposit = new BigNumber(raw.deposit);
        account.withdraw = new BigNumber(raw.withdraw);
        account.allocated = new BigNumber(raw.allocated);
        account.deallocated = new BigNumber(raw.deallocated);
        account.transaction = raw.transaction;
        account.accountSource = raw.accountSource;
        return account;
    }
}

export class DepositPartyA {
    id?: string;
    account?: string;
    amount?: BigNumber;
    timestamp?: BigNumber;
    blockNumber?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): DepositPartyA {
        const depositPartyA = new DepositPartyA();
        depositPartyA.id = raw.id;
        depositPartyA.account = raw.account;
        depositPartyA.amount = new BigNumber(raw.amount);
        depositPartyA.timestamp = new BigNumber(raw.timestamp);
        depositPartyA.blockNumber = new BigNumber(raw.blockNumber);
        depositPartyA.transaction = raw.transaction;
        return depositPartyA;
    }
}

export class WithdrawPartyA {
    id?: string;
    account?: string;
    amount?: BigNumber;
    timestamp?: BigNumber;
    blockNumber?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): WithdrawPartyA {
        const withdrawPartyA = new WithdrawPartyA();
        withdrawPartyA.id = raw.id;
        withdrawPartyA.account = raw.account;
        withdrawPartyA.amount = new BigNumber(raw.amount);
        withdrawPartyA.timestamp = new BigNumber(raw.timestamp);
        withdrawPartyA.blockNumber = new BigNumber(raw.blockNumber);
        withdrawPartyA.transaction = raw.transaction;
        return withdrawPartyA;
    }
}

export class AllocatedPartyA {
    id?: string;
    account?: string;
    amount?: BigNumber;
    timestamp?: BigNumber;
    blockNumber?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): AllocatedPartyA {
        const allocatedPartyA = new AllocatedPartyA();
        allocatedPartyA.id = raw.id;
        allocatedPartyA.account = raw.account;
        allocatedPartyA.amount = new BigNumber(raw.amount);
        allocatedPartyA.timestamp = new BigNumber(raw.timestamp);
        allocatedPartyA.blockNumber = new BigNumber(raw.blockNumber);
        allocatedPartyA.transaction = raw.transaction;
        return allocatedPartyA;
    }
}

export class DeallocatePartyA {
    id?: string;
    account?: string;
    amount?: BigNumber;
    timestamp?: BigNumber;
    blockNumber?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): DeallocatePartyA {
        const deallocatePartyA = new DeallocatePartyA();
        deallocatePartyA.id = raw.id;
        deallocatePartyA.account = raw.account;
        deallocatePartyA.amount = new BigNumber(raw.amount);
        deallocatePartyA.timestamp = new BigNumber(raw.timestamp);
        deallocatePartyA.blockNumber = new BigNumber(raw.blockNumber);
        deallocatePartyA.transaction = raw.transaction;
        return deallocatePartyA;
    }
}

export class TradeHistory {
    id?: string;
    account?: string;
    volume?: BigNumber;
    timestamp?: BigNumber;
    blockNumber?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): TradeHistory {
        const tradeHistory = new TradeHistory();
        tradeHistory.id = raw.id;
        tradeHistory.account = raw.account;
        tradeHistory.volume = new BigNumber(raw.volume);
        tradeHistory.timestamp = new BigNumber(raw.timestamp);
        tradeHistory.blockNumber = new BigNumber(raw.blockNumber);
        tradeHistory.transaction = raw.transaction;
        return tradeHistory;
    }
}

export class Quote {
    id?: string;
    account?: string;
    partyBsWhiteList?: string[];
    symbolId?: BigNumber;
    positionType?: number;
    orderType?: number;
    price?: BigNumber;
    marketPrice?: BigNumber;
    deadline?: BigNumber;
    quantity?: BigNumber;
    cva?: BigNumber;
    mm?: BigNumber;
    lf?: BigNumber;
    maxInterestRate?: BigNumber;
    quoteStatus?: number;
    blockNumber?: BigNumber;
    timestamp?: BigNumber;
    transaction?: string;

    static fromRawObject(raw: any): Quote {
        const quote = new Quote();
        quote.id = raw.id;
        quote.account = raw.account;
        quote.partyBsWhiteList = raw.partyBsWhiteList?.split(",");
        quote.symbolId = new BigNumber(raw.symbolId);
        quote.positionType = parseInt(raw.positionType);
        quote.orderType = parseInt(raw.orderType);
        quote.price = new BigNumber(raw.price);
        quote.marketPrice = new BigNumber(raw.marketPrice);
        quote.deadline = new BigNumber(raw.deadline);
        quote.quantity = new BigNumber(raw.quantity);
        quote.cva = new BigNumber(raw.cva);
        quote.mm = new BigNumber(raw.mm);
        quote.lf = new BigNumber(raw.lf);
        quote.maxInterestRate = new BigNumber(raw.maxInterestRate);
        quote.quoteStatus = parseInt(raw.quoteStatus);
        quote.blockNumber = new BigNumber(raw.blockNumber);
        quote.timestamp = new BigNumber(raw.timestamp);
        quote.transaction = raw.transaction;
        return quote;
    }
}

export class DailyHistory {
    id?: string;
    quotesCount?: BigNumber;
    tradeVolume?: BigNumber;
    deposit?: BigNumber;
    withdraw?: BigNumber;
    allocate?: BigNumber;
    deallocate?: BigNumber;
    activeUsers?: BigNumber;
    newUsers?: BigNumber;
    newAccounts?: BigNumber;
    platformFee?: BigNumber;
    openInterest?: BigNumber;
    accountSource?: string;

    static fromRawObject(raw: any): DailyHistory {
        const dailyHistory = new DailyHistory();
        dailyHistory.id = raw.id;
        dailyHistory.quotesCount = new BigNumber(raw.quotesCount);
        dailyHistory.tradeVolume = new BigNumber(raw.tradeVolume);
        dailyHistory.deposit = new BigNumber(raw.deposit);
        dailyHistory.withdraw = new BigNumber(raw.withdraw);
        dailyHistory.allocate = new BigNumber(raw.allocate);
        dailyHistory.deallocate = new BigNumber(raw.deallocate);
        dailyHistory.newUsers = new BigNumber(raw.newUsers);
        dailyHistory.activeUsers = new BigNumber(raw.activeUsers);
        dailyHistory.newAccounts = new BigNumber(raw.newAccounts);
        dailyHistory.platformFee = new BigNumber(raw.platformFee);
        dailyHistory.openInterest = new BigNumber(raw.openInterest);
        dailyHistory.accountSource = raw.accountSource;
        return dailyHistory;
    }

    public static getTime(dh: DailyHistory): number | null {
        if (dh.id != null)
            return Number(dh.id?.split("_")[0])
        return null;
    }
}
