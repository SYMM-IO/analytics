import {Affiliate} from "../environments/environment-interface"
import {DailyHistory} from "./models"

export type AffiliateHistory = { affiliate: Affiliate, histories: DailyHistory[] }