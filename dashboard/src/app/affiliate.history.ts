import {Affiliate} from "../environments/environment-interface"
import {DailyHistory, MonthlyHistory, WeeklyHistory} from "./models"

export type AffiliateHistory = {
	affiliate: Affiliate,
	histories: DailyHistory[],
	weeklyHistories: WeeklyHistory[],
	monthlyHistories: MonthlyHistory[]
}