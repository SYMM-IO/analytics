import {DailyHistory} from "./services/graph-models"
import BigNumber from "bignumber.js"

export function aggregateDailyHistories(histories: DailyHistory[], decimalsMap: Map<string, number> | undefined = undefined): DailyHistory {
    const keys = [
        "quotesCount",
        "tradeVolume",
        "deposit",
        "withdraw",
        "allocate",
        "deallocate",
        "activeUsers",
        "newUsers",
        "newAccounts",
        "platformFee",
        "openInterest"
    ]
    const withDecimalsKeys = [
        "deposit",
        "withdraw",
    ]
    let base = new DailyHistory()
    base.id = histories[0].id
    return histories.reduce((accumulator: DailyHistory, current: DailyHistory) => {
        for (const key of keys) {
            let value = current[key] as BigNumber
            if (decimalsMap != null && withDecimalsKeys.indexOf(key) >= 0) {
                const accountSource = current.accountSource!
                const decimals = decimalsMap.get(accountSource)!
                value = BigNumber(value!).times(BigNumber(10).pow(18 - decimals))
            }
            const accValue = accumulator[key] as BigNumber || BigNumber(0)
            accumulator[key] = accValue.plus(value as BigNumber)
        }
        return accumulator
    }, base)
}