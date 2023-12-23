import {Affiliate} from "../environments/environment-interface"
import {DailyHistory} from "./services/graph-models"

export type AffiliateHistory = { affiliate: Affiliate, histories: DailyHistory[] }