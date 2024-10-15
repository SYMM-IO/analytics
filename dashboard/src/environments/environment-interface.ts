import BigNumber from "bignumber.js"

export enum Version {
	V_0_8_0,
	LATEST,
}

export interface EnvironmentInterface {
	name: string
	collaterals?: string[]
	collateralDecimal?: number
	affiliates?: Affiliate[]
	solvers?: Solver[]
	subgraphUrl?: string
	assetsFolder?: string
	panel?: boolean
	serverUrl?: string
	version?: Version
	startDate?: Date
	environments?: EnvironmentInterface[]
}

export interface GroupIndex {
	id?: number
	name?: string
	address?: string
	mainColor?: string
}

export enum AffiliateName {
	INTENTX = "IntentX",
	THENA = "Thena",
	BEFI = "BeFi",
	CLOVERFIELD = "Cloverfield",
	CORE = "Core",
	BMX = "BMX",
	PRIVEX = "Privex",
	PEAR = "Pear",
	BASED = "Based",
}

export let affiliateColors = new Map<AffiliateName, string>()
affiliateColors.set(AffiliateName.INTENTX, "#F20C27")
affiliateColors.set(AffiliateName.BEFI, "#FE9E0F")
affiliateColors.set(AffiliateName.CLOVERFIELD, "#A2D4EA")
affiliateColors.set(AffiliateName.CORE, "#C8C903")
affiliateColors.set(AffiliateName.BMX, "#1F61B5")
affiliateColors.set(AffiliateName.PRIVEX, "#0000ff")
affiliateColors.set(AffiliateName.PEAR, "#ace075")
affiliateColors.set(AffiliateName.BASED, "#F5B3F7")
affiliateColors.set(AffiliateName.THENA, "#ED00C9")

export interface Affiliate extends GroupIndex {
	name?: AffiliateName
	mainColor?: string
	address?: string
	fromTimestamp: string | null
	depositDiff?: BigNumber
}

export enum SolverName {
	PERPS_HUB = "PerpsHub",
	RASA = "Rasa",
	ZENITH = "Zenith",
}

export let solverColors = new Map<SolverName, string>()
solverColors.set(SolverName.PERPS_HUB, "#ff6e7f")
solverColors.set(SolverName.RASA, "#A2D4EA")
solverColors.set(SolverName.ZENITH, "#e9de7d")

export interface Solver extends GroupIndex {
	name?: string
	address?: string
	mainColor?: string
}
