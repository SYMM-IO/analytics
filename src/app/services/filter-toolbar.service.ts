import { Injectable } from "@angular/core"
import { BehaviorSubject } from "rxjs"
import BigNumber from "bignumber.js"

export type DashboardView = "FRONTENDS" | "SOLVERS"

export const OTHERS_FRONTEND_NAME = "Others"
export const OTHERS_FRONTEND_COLOR = "#9a60b4"

/**
 * Shared state for the global filter toolbar (chains, frontends, view scope).
 *
 * Owns the canonical selection so that AppComponent can render the filter pills
 * inside the app's top toolbar while HomeComponent (and its children) consume
 * the same state to drive charts/info-cards.
 *
 * HomeComponent calls `setLoadedChains` / `setIgnoredChains` /
 * `setAvailableFrontends` to feed availability; the service handles the
 * "customized" tracking and pruning.
 */
@Injectable({ providedIn: "root" })
export class FilterToolbarService {
	private static readonly FRONTEND_GROUPING_THRESHOLD = BigNumber(100_000).times(BigNumber(10).pow(18))
	private static readonly COMPACT_USD_FORMATTER = new Intl.NumberFormat("en-US", {
		style: "currency",
		currency: "USD",
		notation: "compact",
		maximumFractionDigits: 2,
	})

	readonly visible$ = new BehaviorSubject<boolean>(false)

	readonly loadedChainNames$ = new BehaviorSubject<string[]>([])
	readonly ignoredChainNames$ = new BehaviorSubject<string[]>([])
	readonly selectedChainNames$ = new BehaviorSubject<string[]>([])

	readonly availableFrontendNames$ = new BehaviorSubject<string[]>([])
	readonly selectedFrontendNames$ = new BehaviorSubject<string[]>([])
	readonly lowVolumeFrontendNames$ = new BehaviorSubject<ReadonlySet<string>>(new Set())

	readonly view$ = new BehaviorSubject<DashboardView>("FRONTENDS")

	hasCustomizedChainSelection = false
	hasCustomizedFrontendSelection = false
	private frontendVolumesByName = new Map<string, string>()

	chainDropdownOpen = false
	frontendDropdownOpen = false

	get view(): DashboardView { return this.view$.value }
	setView(view: DashboardView): void {
		if (this.view$.value === view) return
		this.view$.next(view)
		// Frontend filter is meaningless in solver view — close any open dropdown.
		if (view === "SOLVERS") this.frontendDropdownOpen = false
	}

	get loadedChainNames(): string[] { return this.loadedChainNames$.value }
	get ignoredChainNames(): string[] { return this.ignoredChainNames$.value }
	get selectedChainNames(): string[] { return this.selectedChainNames$.value }
	get availableFrontendNames(): string[] { return this.availableFrontendNames$.value }
	get selectedFrontendNames(): string[] { return this.selectedFrontendNames$.value }
	get visible(): boolean { return this.visible$.value }

	setVisible(value: boolean): void {
		if (this.visible$.value !== value) this.visible$.next(value)
		if (!value) {
			this.chainDropdownOpen = false
			this.frontendDropdownOpen = false
		}
	}

	setLoadedChains(names: string[]): void {
		this.loadedChainNames$.next(names)
		if (!this.hasCustomizedChainSelection) {
			this.selectedChainNames$.next([...names])
		} else {
			const loadedSet = new Set(names)
			this.selectedChainNames$.next(this.selectedChainNames.filter(n => loadedSet.has(n)))
		}
	}

	setIgnoredChains(names: string[]): void {
		this.ignoredChainNames$.next(names)
	}

	setAvailableFrontends(names: string[]): void {
		this.availableFrontendNames$.next(names)
		if (!this.hasCustomizedFrontendSelection) {
			this.selectedFrontendNames$.next([...names])
		} else {
			const set = new Set(names)
			this.selectedFrontendNames$.next(this.selectedFrontendNames.filter(n => set.has(n)))
		}
	}

	setFrontendVolumes(volumes: Map<string, string>): void {
		const lowVolumeNames = new Set<string>()
		for (const [name, rawVolume] of volumes) {
			const volume = BigNumber(rawVolume)
			if (volume.gt(0) && volume.lt(FilterToolbarService.FRONTEND_GROUPING_THRESHOLD)) lowVolumeNames.add(name)
		}

		const groupedVolumes = new Map<string, BigNumber>()
		for (const [name, rawVolume] of volumes) {
			const displayName = lowVolumeNames.has(name) ? OTHERS_FRONTEND_NAME : name
			groupedVolumes.set(displayName, (groupedVolumes.get(displayName) ?? BigNumber(0)).plus(rawVolume))
		}

		this.frontendVolumesByName = new Map(
			[...groupedVolumes.entries()].map(([name, volume]) => [name, volume.toFixed()]),
		)
		if (!this.setsEqual(this.lowVolumeFrontendNames$.value, lowVolumeNames)) {
			this.lowVolumeFrontendNames$.next(lowVolumeNames)
		}
	}

	frontendDisplayName(name: string | undefined): string | undefined {
		return name && this.lowVolumeFrontendNames$.value.has(name) ? OTHERS_FRONTEND_NAME : name
	}

	frontendVolume(name: string): string {
		const volume = this.frontendVolumesByName.get(name)
		const normalizedVolume = volume === undefined ? undefined : BigNumber(volume).div(BigNumber(10).pow(18))
		return normalizedVolume === undefined ? "—" : FilterToolbarService.COMPACT_USD_FORMATTER.format(normalizedVolume.toNumber())
	}

	hasFrontendTradeVolume(name: string): boolean {
		return BigNumber(this.frontendVolumesByName.get(name) ?? 0).gt(0)
	}

	toggleChainDropdown(): void {
		if (this.loadedChainNames.length === 0 && this.ignoredChainNames.length === 0) return
		this.chainDropdownOpen = !this.chainDropdownOpen
		if (this.chainDropdownOpen) this.frontendDropdownOpen = false
	}

	toggleFrontendDropdown(): void {
		if (this.availableFrontendNames.length === 0) return
		this.frontendDropdownOpen = !this.frontendDropdownOpen
		if (this.frontendDropdownOpen) this.chainDropdownOpen = false
	}

	closeDropdowns(): void {
		this.chainDropdownOpen = false
		this.frontendDropdownOpen = false
	}

	toggleChain(name: string): void {
		const set = new Set(this.selectedChainNames)
		if (set.has(name)) set.delete(name)
		else set.add(name)
		this.hasCustomizedChainSelection = true
		this.selectedChainNames$.next(this.loadedChainNames.filter(n => set.has(n)))
	}

	selectAllChains(): void {
		this.hasCustomizedChainSelection = false
		this.selectedChainNames$.next([...this.loadedChainNames])
	}

	clearChainSelection(): void {
		this.hasCustomizedChainSelection = true
		this.selectedChainNames$.next([])
	}

	isChainSelected(name: string): boolean {
		return this.selectedChainNames.includes(name)
	}

	toggleFrontend(name: string): void {
		const set = new Set(this.selectedFrontendNames)
		if (set.has(name)) set.delete(name)
		else set.add(name)
		this.hasCustomizedFrontendSelection = true
		this.selectedFrontendNames$.next(this.availableFrontendNames.filter(n => set.has(n)))
	}

	selectAllFrontends(): void {
		this.hasCustomizedFrontendSelection = false
		this.selectedFrontendNames$.next([...this.availableFrontendNames])
	}

	clearFrontendSelection(): void {
		this.hasCustomizedFrontendSelection = true
		this.selectedFrontendNames$.next([])
	}

	isFrontendSelected(name: string): boolean {
		return this.selectedFrontendNames.includes(name)
	}

	private static readonly CHAIN_LOGOS: Record<string, string> = {
		fantom: "assets/chains/fantom.svg",
		bnb: "assets/chains/binance.svg",
		binance: "assets/chains/binance.svg",
		base: "assets/chains/base.png",
		blast: "assets/chains/blast.svg",
		mantle: "assets/chains/mantle.svg",
		arbitrum: "assets/chains/arbitrum.png",
		sonic: "assets/chains/sonic.svg",
		hyperevm: "assets/chains/hyperevm.svg",
	}

	private static readonly FRONTEND_LOGOS: Record<string, string> = {
		intentx: "assets/frontends/intentx-rounded-branded.svg",
		thena: "assets/frontends/thena-rounded-branded.svg",
		befi: "assets/frontends/befi-labs-rounded-branded.svg",
		cloverfield: "assets/frontends/cloverfield-rounded-branded.svg",
		core: "assets/frontends/core-rounded-branded.svg",
		bmx: "assets/frontends/bmx-rounded-branded.svg",
		privex: "assets/frontends/privex-rounded-branded.svg",
		pear: "assets/frontends/pear-rounded-branded.svg",
		based: "assets/frontends/based-rounded-branded.svg",
		xpanse: "assets/frontends/xpanse-rounded-branded.svg",
		ivx: "assets/frontends/ivx-rounded-branded.svg",
		lode: "assets/frontends/lode-rounded-branded.svg",
		spooky: "assets/frontends/spooky-rounded-branded.svg",
		vibe: "assets/frontends/vibe-rounded-branded.svg",
		carbon: "assets/frontends/carbon-rounded-branded.svg",
		quickswap: "assets/frontends/quickswap-rounded-branded.svg",
		treble: "assets/frontends/treble-rounded-branded.svg",
	}

	chainLogo(name: string): string | null {
		return FilterToolbarService.CHAIN_LOGOS[name.toLowerCase()] ?? null
	}

	frontendLogo(name: string): string | null {
		return FilterToolbarService.FRONTEND_LOGOS[name.toLowerCase()] ?? null
	}

	chainInitials(name: string): string {
		return name.slice(0, 2).toUpperCase()
	}

	private setsEqual(a: ReadonlySet<string>, b: ReadonlySet<string>): boolean {
		return a.size === b.size && [...a].every(value => b.has(value))
	}
}
