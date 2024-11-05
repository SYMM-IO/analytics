import { Affiliate, Solver } from "../environments/environment-interface"
import { DailyHistory, MonthlyHistory, SolverDailyHistory, WeeklyHistory } from "./models"

export type GroupedHistory = {
	index: Affiliate | Solver
	dailyHistories: DailyHistory[] | SolverDailyHistory[]
	weeklyHistories: WeeklyHistory[]
	monthlyHistories: MonthlyHistory[]
}
