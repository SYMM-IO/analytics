import { Component, ElementRef, HostListener, Input, OnDestroy, OnInit, ViewChild } from "@angular/core"
import { EChartsOption } from "echarts"
import { Observable, Subscription } from "rxjs"
import { DailyHistory, MonthlyHistory, WeeklyHistory } from "../models"
import BigNumber from "bignumber.js"
import { StateService } from "../services/state.service"
import { GroupedHistory } from "../groupedHistory"
import { tuiItemsHandlersProvider } from "@taiga-ui/kit"
import { FormControl } from "@angular/forms"
import { TuiDay } from "@taiga-ui/cdk"
import { CallbackDataParams } from "echarts/types/dist/shared"

const stringifier = (item: any): string => item.name || item

@Component({
    selector: "app-chart",
    templateUrl: "./chart.component.html",
    styleUrls: ["./chart.component.scss"],
    providers: [tuiItemsHandlersProvider({ stringify: stringifier })],
    standalone: false
})
export class ChartComponent implements OnInit, OnDestroy {
	@ViewChild("chart") chartElement!: ElementRef
	@Input() fieldName!: string
	@Input() fixedValueName?: string
	@Input() decimals = 0
	@Input() chartTitle!: string
	@Input() yAxisFormatter: (x: any) => string = a => a
	@Input() tooltipFormatter?: any
	@Input() hasGroupByMonthAction = true
	@Input() hasCumulative = true
	@Input() partyBVolumeIncluded: boolean | undefined = undefined
	@Input() groupedHistories!: Observable<GroupedHistory[]>

	chartOption?: EChartsOption
	chart: any
	loadedResults?: GroupedHistory[]
	groupedByMonth = false
	showPartyBVolume = true
	cumulativeMode = false
	viewOptions: string[] = ["Daily"]
	selectedView = new FormControl("Daily")
	intervalOptions: readonly any[] = [
		{ days: 30, name: "1M" },
		{ days: 90, name: "3M" },
		{ days: 180, name: "6M" },
		{ days: 365, name: "1Y" },
		{ days: 730, name: "All" },
		{ days: 0, name: "Custom" },
	]
	intervalOptionsStringify = stringifier
	intervalForm = new FormControl(this.intervalOptions[1])
	intervalRangeForm = new FormControl()
	readonly intervalRangeMin = new TuiDay(2000, 2, 20)
	readonly intervalRangeMax = new TuiDay(2040, 2, 20)

	startTime = Date.now() - this.interval
	endTime = Date.now()
	minTime = Number.MAX_SAFE_INTEGER
	maxTime = 0
	visibleSeries: string[] = []
	
	// Custom legend properties
	allSeries: Array<{ name: string; color: string }> = []
	selectedSeries: Set<string> = new Set()
	legendDropdownOpen = false

	private subscriptions: Subscription[] = []

	constructor(readonly stateService: StateService) {}

	ngOnInit(): void {
		this.initChartOptions()
		this.subscribeToFormChanges()
	}

	ngOnDestroy() {
		this.subscriptions.forEach(sub => sub.unsubscribe())
	}

	onChartInit(chart: any) {
		this.chart = chart
		this.subscribeToDataChanges()
		this.setupChartEventListeners()
	}

	onGroupByMonthChanged() {
		this.groupedByMonth = !this.groupedByMonth
		this.updateChartIfDataAvailable()
	}

	onShowPartyBVolumeChanged() {
		this.showPartyBVolume = !this.showPartyBVolume
		this.updateChartIfDataAvailable()
	}

	toggleCumulative() {
		this.cumulativeMode = !this.cumulativeMode
		this.updateChartIfDataAvailable()
	}

	isCumulativeSelected(): boolean {
		return this.cumulativeMode
	}

	goBack() {
		this.endTime = this.startTime
		this.startTime = this.startTime - this.interval
		this.updateChartIfDataAvailable()
	}

	goForward() {
		this.startTime = this.endTime
		this.endTime = this.endTime + this.interval
		this.updateChartIfDataAvailable()
	}

	onResize(event: DOMRectReadOnly) {
		if (this.chart) {
			this.chart.resize({
				width: event.width - 35,
				height: event.height - 20,
			})
		}
	}

	private initChartOptions() {
		this.chartOption = {
			progressive: 300,
			progressiveThreshold: 500,
			backgroundColor: "transparent",
			color: ["#3398DB", "#7CFC00", "#FF7F50", "#8B0000", "#D2691E"],
			grid: { left: "60", right: "20", top: "15", bottom: "0" },
			autoResize: true,
			darkMode: true,
			xAxis: {
				type: "time",
				axisPointer: {
					snap: true,
					lineStyle: {
						color: "#ffffff",
						width: 1,
					},
				},
			},
			yAxis: {
				type: "value",
				splitNumber: 4,
				axisLabel: {
					formatter: this.formatYAxisLabel,
				},
			},
			title: { show: false },
			animationDelay: function (idx) {
				// delay for later data is larger
				return idx * 3
			},
			tooltip: {
				trigger: "axis",
				appendTo: undefined,
				confine: true,
				renderMode: "html",
				axisPointer: {
					type: "line",
				},
				formatter: (params: CallbackDataParams | CallbackDataParams[]) => {
					return this.formatTooltip(Array.isArray(params) ? params : [params])
				},
				backgroundColor: "rgba(54,54,54,0.9)",
				borderWidth: 0, // Remove border
				padding: [5, 10],
				textStyle: {
					color: "#ffffff",
				},
				extraCssText: "box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);", // Add shadow for depth
				triggerOn: "mousemove|click",
			},
			legend: {
				show: false, // Hide default legend, we'll use custom one
			},
			toolbox: { show: false },
			dataZoom: [{ type: "inside", throttle: 50 }],
		}
	}

	private subscribeToFormChanges() {
		const subscription = this.intervalForm.valueChanges.subscribe(() => this.handleIntervalChange())
		this.subscriptions.push(subscription)

		const rangeSubscription = this.intervalRangeForm.valueChanges.subscribe(() => this.handleIntervalChange())
		this.subscriptions.push(rangeSubscription)

		const viewSubscription = this.selectedView.valueChanges.subscribe(() => this.updateChartIfDataAvailable())
		this.subscriptions.push(viewSubscription)
	}

	private handleIntervalChange() {
		if (this.updateRange() && this.loadedResults != null) {
			this.updateChart(this.loadedResults, this.fieldName)
		}
	}

	private subscribeToDataChanges() {
		const subscription = this.groupedHistories.subscribe(results => {
			this.loadedResults = results
			this.determineViewOptions()
			this.updateChart(results, this.fieldName)
		})
		this.subscriptions.push(subscription)
	}

	private setupChartEventListeners() {
		this.chart.on("legendselectchanged", (params: any) => {
			// Update selectedSeries based on ECharts legend changes
			Object.keys(params.selected).forEach(seriesName => {
				if (params.selected[seriesName]) {
					this.selectedSeries.add(seriesName)
				} else {
					this.selectedSeries.delete(seriesName)
				}
			})
			this.visibleSeries = Array.from(this.selectedSeries)
			this.updateChartIfDataAvailable()
		})
	}

	private determineViewOptions(): void {
		this.viewOptions = ["Daily"]
		if (this.loadedResults && this.loadedResults.length > 0) {
			const sampleWeeklyHistory = this.loadedResults[this.loadedResults.length - 1].weeklyHistories[0]
			const sampleMonthlyHistory = this.loadedResults[this.loadedResults.length - 1].monthlyHistories[0]
			if (sampleWeeklyHistory && this.fieldName in sampleWeeklyHistory) {
				this.viewOptions.push("Weekly")
			}
			if (sampleMonthlyHistory && this.fieldName in sampleMonthlyHistory) {
				this.viewOptions.push("Monthly")
			}
		}
		if (!this.viewOptions.includes(this.selectedView.value!)) {
			this.selectedView.setValue("Daily")
		}
	}

	private updateChartIfDataAvailable() {
		if (this.loadedResults) {
			this.updateChart(this.loadedResults, this.fieldName)
		}
	}

	private updateChart(groupedHistories: GroupedHistory[], fieldName: string) {
		const series = this.prepareSeries(groupedHistories, fieldName)
		
		// Get colors from chart option
		const colors = this.chartOption?.color as string[] || ["#3398DB", "#7CFC00", "#FF7F50", "#8B0000", "#D2691E"]
		
		// Update allSeries with current series data
		this.allSeries = series.map((s: any, index: number) => ({
			name: s.name,
			color: s.color || colors[index % colors.length] || colors[0],
		}))
		
		// Initialize selectedSeries if empty (first load)
		if (this.selectedSeries.size === 0) {
			this.allSeries.forEach(s => {
				this.selectedSeries.add(s.name)
			})
		}
		
		// Update visibleSeries based on selectedSeries
		this.visibleSeries = Array.from(this.selectedSeries)
		
		// Build selected object for ECharts
		const selected: Record<string, boolean> = {}
		this.allSeries.forEach(s => {
			selected[s.name] = this.selectedSeries.has(s.name)
		})
		
		this.chart.setOption(
			{
				series: series,
				legend: {
					selected: selected,
				},
				xAxis: {
					type: "time",
					axisLabel: {
						formatter: (value: number) => this.formatXAxisLabel(value, this.selectedView.value!),
					},
				},
			},
			false,
			false,
		)
	}

	private prepareSeries(groupedHistories: GroupedHistory[], fieldName: string) {
		const series = []
		const view = this.selectedView.value
		// Always include all series - visibility is controlled by ECharts legend selection
		for (const groupHistory of groupedHistories) {
			const preparedResults = this.prepareResults(this.getHistoryByView(groupHistory, view!), fieldName)
			series.push(this.createSeriesItem(groupHistory, preparedResults, fieldName, view!))
		}
		return series
	}

	private getHistoryByView(groupedHistory: GroupedHistory, view: string) {
		switch (view) {
			case "Daily":
				return groupedHistory.dailyHistories
			case "Weekly":
				return groupedHistory.weeklyHistories
			case "Monthly":
				return groupedHistory.monthlyHistories
			default:
				return groupedHistory.dailyHistories
		}
	}

	private createSeriesItem(groupedHistory: GroupedHistory, preparedResults: any, fieldName: string, view: string) {
		let data = preparedResults.data.map((history: any) => {
			return [new Date(this.getTimeByView(history, view)), (history[fieldName] as BigNumber).div(BigNumber(10).pow(this.decimals)).toNumber()]
		})
		
		// If cumulative mode is enabled, make the values cumulative
		if (this.cumulativeMode) {
			let runningTotal = 0
			data = data.map(([date, value]: [Date, number]) => {
				runningTotal += value
				return [date, runningTotal]
			})
		}
		
		return {
			type: "bar",
			stack: fieldName.match("average") == null ? "total" : undefined,
			color: groupedHistory.index.mainColor,
			name: this.fixedValueName || groupedHistory.index.name,
			data: data,
			animation: true,
		}
	}

	private getTimeByView(history: any, view: string): number {
		switch (view) {
			case "Daily":
				return DailyHistory.getTime(history)!
			case "Weekly":
				return WeeklyHistory.getTime(history)!
			case "Monthly":
				return MonthlyHistory.getTime(history)!
			default:
				return DailyHistory.getTime(history)!
		}
	}

	private prepareResults(histories: any[], fieldName: string) {
		let data = histories
			.filter(history => {
				const time = this.getTimeByView(history, this.selectedView.value!)
				this.minTime = Math.min(this.minTime, time)
				this.maxTime = Math.max(this.maxTime, time)
				return time > this.startTime && time <= this.endTime
			})
			.map(history => ({ ...history }))

		if (this.showPartyBVolume == true && this.partyBVolumeIncluded == false) {
			data = data.map(h => {
				const time = this.getTimeByView(h, this.selectedView.value!)
				if (time > 1723852800000) {
					h[fieldName] = h[fieldName].times(BigNumber(2))
				}
				return h
			})
		} else if (this.showPartyBVolume == false && this.partyBVolumeIncluded == true) {
			data = data.map(h => {
				const time = this.getTimeByView(h, this.selectedView.value!)
				if (time > 1723852800000) {
					h[fieldName] = h[fieldName].div(BigNumber(2))
				}
				return h
			})
		}

		if (this.groupedByMonth) {
			data = this.groupDataByMonth(data, fieldName)
		}

		return { data }
	}

	private groupDataByMonth(data: any[], fieldName: string) {
		return Object.values(
			data.reduce((acc: any, curr: any) => {
				const date = new Date(this.getTimeByView(curr, this.selectedView.value!))
				const yearMonth = new Date(date.getFullYear(), date.getMonth(), 1, 0, 0, 0, 0).getTime()
				if (!acc[yearMonth]) {
					acc[yearMonth] = { id: yearMonth + "_", [fieldName]: BigNumber(0) }
				}
				acc[yearMonth][fieldName] = acc[yearMonth][fieldName].plus(curr[fieldName]!)
				return acc
			}, {}),
		)
	}

	private get interval(): number {
		if (!this.intervalForm) return 0
		const optionValue = this.intervalForm.value.days
		return optionValue > 0 ? optionValue * 24 * 60 * 60 * 1000 : this.intervalRangeForm.value
	}

	private updateRange(): boolean {
		const optionValue = this.intervalForm.value.days
		if (optionValue > 0) {
			this.endTime = Date.now()
			this.startTime = this.endTime - this.interval
			return true
		} else if (this.intervalRangeForm.value) {
			this.endTime = (this.intervalRangeForm.value.to as TuiDay).toUtcNativeDate().getTime() + 1
			this.startTime = (this.intervalRangeForm.value.from as TuiDay).toUtcNativeDate().getTime() - 1
			return true
		}
		return false
	}

	private formatYAxisLabel(value: number): string {
		if (value >= 1e9) return (value / 1e9).toFixed(2) + "B"
		if (value >= 1e6) return (value / 1e6).toFixed(2) + "M"
		if (value >= 1e3) return (value / 1e3).toFixed(2) + "K"
		return value.toString()
	}

	private formatTooltip(params: CallbackDataParams[]): string {
		if (params.length === 0) return ""

		const dateValue = params[0]?.value
		let dateString = "N/A"
		if (Array.isArray(dateValue) && dateValue[0] != null) {
			dateString = new Date(dateValue[0] as number).toLocaleDateString()
		} else if (typeof dateValue === "number") {
			dateString = new Date(dateValue).toLocaleDateString()
		}

		// Filter items with values > 0 and calculate sum
		let sum = 0
		const validItems: Array<{ color: string; name: string; value: number }> = []

		params.forEach(item => {
			const color = item.color as string
			let value: number = 0
			if (Array.isArray(item.value) && item.value[1] != null) {
				value = Number(item.value[1])
			} else if (typeof item.value === "number") {
				value = item.value
			}
			sum += value
			if (value > 0) {
				validItems.push({
					color,
					name: item.seriesName || "Cloverfield",
					value,
				})
			}
		})

		// Determine if we need multi-column layout
		const useMultiColumn = validItems.length > 8
		const columnCount = validItems.length > 16 ? 3 : validItems.length > 8 ? 2 : 1

		let content = `
      <div style="font-family: Arial, sans-serif; padding: 10px; border-radius: 5px; border: 0; max-width: ${useMultiColumn ? "600px" : "300px"};">
        <div style="font-size: 14px; color: #ffffff; margin-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.2); padding-bottom: 5px;">
          <strong>${dateString}</strong>
        </div>
        <div style="max-height: 350px; overflow-y: auto; overflow-x: hidden;">
          <div style="display: grid; grid-template-columns: repeat(${columnCount}, 1fr); gap: 2px 15px;">
    `

		validItems.forEach(item => {
			content += `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 3px 5px; min-width: 0;">
              <div style="display: flex; align-items: center; min-width: 0; flex: 1; margin-right: 8px;">
                <span style="flex-shrink: 0; width: 10px; height: 10px; background-color: ${item.color}; border-radius: 50%; margin-right: 5px;"></span>
                <span style="color: #cccccc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${item.name}</span>
              </div>
              <span style="color: #ffffff; font-weight: bold; white-space: nowrap;">${this.yAxisFormatter(item.value)}</span>
            </div>
			`
		})

		content += `
          </div>
        </div>
    `

		// Add Aggregated row
		if (this.fieldName.match("average") == null)
			content += `
        <div style="border-top: 1px solid rgba(255, 255, 255, 0.2); margin-top: 8px; padding-top: 8px; display: flex; justify-content: space-between;">
          <span style="color: #cccccc;"><strong>Aggregated</strong></span>
          <span style="color: #ffffff; font-weight: bold;">${this.yAxisFormatter(sum)}</span>
        </div>
    `

		content += `
      </div>
    `

		return content
	}

	private formatXAxisLabel(value: number, view: string): string {
		const date = new Date(value)
		switch (view) {
			case "Daily":
				return this.formatDailyDate(date)
			case "Weekly":
				return this.getWeekDisplay(date)
			case "Monthly":
				return date.toLocaleDateString("default", { month: "short", year: "numeric" })
			default:
				return date.toLocaleDateString()
		}
	}

	private formatDailyDate(date: Date): string {
		const now = new Date()
		const diffTime = Math.abs(now.getTime() - date.getTime())
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

		if (diffDays < 1) {
			return "Today"
		} else if (diffDays < 2) {
			return "Yesterday"
		} else if (diffDays < 7) {
			return date.toLocaleDateString("default", { weekday: "short" })
		} else if (date.getFullYear() === now.getFullYear()) {
			return date.toLocaleDateString("default", { month: "short", day: "numeric" })
		} else {
			return date.toLocaleDateString("default", { year: "numeric", month: "short", day: "numeric" })
		}
	}

	getWeekDisplay(date: Date): string {
		const month = date.toLocaleString("default", { month: "short" })
		const weekOfMonth = this.getWeekOfMonth(date)
		return `${month} W${weekOfMonth}`
	}

	private getWeekOfMonth(date: Date): number {
		const firstDayOfMonth = new Date(date.getFullYear(), date.getMonth(), 1)
		const dayOfWeek = firstDayOfMonth.getDay()
		const offset = dayOfWeek === 0 ? 6 : dayOfWeek - 1 // Adjust for Monday as first day of week

		return Math.ceil((date.getDate() + offset) / 7)
	}
	
	// Custom legend methods
	toggleSeries(seriesName: string) {
		if (this.selectedSeries.has(seriesName)) {
			this.selectedSeries.delete(seriesName)
		} else {
			this.selectedSeries.add(seriesName)
		}
		this.updateChartVisibility()
	}
	
	deselectAll() {
		this.selectedSeries.clear()
		this.updateChartVisibility()
	}
	
	selectAll() {
		this.allSeries.forEach(s => {
			this.selectedSeries.add(s.name)
		})
		this.updateChartVisibility()
	}
	
	isSeriesSelected(seriesName: string): boolean {
		return this.selectedSeries.has(seriesName)
	}
	
	removeSeries(seriesName: string) {
		this.selectedSeries.delete(seriesName)
		this.updateChartVisibility()
	}
	
	private updateChartVisibility() {
		if (!this.chart) return
		
		const selected: Record<string, boolean> = {}
		this.allSeries.forEach(s => {
			selected[s.name] = this.selectedSeries.has(s.name)
		})
		
		this.chart.setOption({
			legend: {
				selected: selected,
			},
		}, false, false)
		
		this.visibleSeries = Array.from(this.selectedSeries)
	}
	
	toggleLegendDropdown() {
		this.legendDropdownOpen = !this.legendDropdownOpen
	}
	
	closeLegendDropdown() {
		this.legendDropdownOpen = false
	}
	
	@HostListener('document:click', ['$event'])
	onDocumentClick(event: MouseEvent) {
		const target = event.target as HTMLElement
		const dropdownContainer = target.closest('.legend-dropdown-container')
		if (!dropdownContainer && this.legendDropdownOpen) {
			this.closeLegendDropdown()
		}
	}
}
