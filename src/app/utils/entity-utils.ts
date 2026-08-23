import { Affiliate, EnvironmentInterface, Solver } from "../../environments/environment-interface"

const NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
const UNKNOWN_NAME = "Unknown"
const UNKNOWN_COLOR = "#5470c6"
const FALLBACK_AFFILIATE_NAMES_BY_ADDRESS = new Map([
	["0x45eecd7b4f442388acd90467e423a5caac3a9c3f", "Trading SDK"],
	["0xa503eb7714d4328f3d425f24954c6f5f00115e09", "Echoes"],
	["0xbb1ad4e9430eb87516774e0079b1529e079a0596", "Bulla"],
])

export function resolveAffiliate(env: EnvironmentInterface, address?: string): Affiliate {
	const normalizedAddress = normalizeAddress(address)
	const existing = env.affiliates?.find(affiliate => normalizeAddress(affiliate.address) === normalizedAddress)
	if (existing) return existing

	const unknown: Affiliate = {
		name: FALLBACK_AFFILIATE_NAMES_BY_ADDRESS.get(normalizedAddress) ?? UNKNOWN_NAME,
		address: normalizedAddress,
		mainColor: UNKNOWN_COLOR,
		fromTimestamp: "0",
	}
	env.affiliates = [...(env.affiliates ?? []), unknown]
	return unknown
}

export function resolveSolver(env: EnvironmentInterface, address?: string): Solver {
	const normalizedAddress = normalizeAddress(address)
	const existing = env.solvers?.find(solver => normalizeAddress(solver.address) === normalizedAddress)
	if (existing) return existing

	const unknown: Solver = {
		name: UNKNOWN_NAME,
		address: normalizedAddress,
		mainColor: UNKNOWN_COLOR,
	}
	env.solvers = [...(env.solvers ?? []), unknown]
	return unknown
}

export function normalizeAddress(address?: string): string {
	return address?.toLowerCase() || NULL_ADDRESS
}
