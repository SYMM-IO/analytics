import { Component, ElementRef, Input, OnDestroy, OnInit, ViewChild } from "@angular/core"
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
	@Input() groupedHistories!: Observable<GroupedHistory[]>

	chartOption?: EChartsOption
	chart: any
	loadedResults?: GroupedHistory[]
	groupedByMonth = false
	showPartyBVolume = true
	viewOptions: string[] = ["Daily"]
	selectedView = new FormControl("Daily")
	intervalOptions: readonly any[] = [
		{ days: 30, name: "1M" },
		{ days: 90, name: "3M" },
		{ days: 180, name: "6M" },
		{ days: 365, name: "1Y" },
		{ days: 0, name: "Custom" },
	]
	intervalOptionsStringify = stringifier
	intervalForm = new FormControl(this.intervalOptions[2])
	intervalRangeForm = new FormControl()
	readonly intervalRangeMin = new TuiDay(2000, 2, 20)
	readonly intervalRangeMax = new TuiDay(2040, 2, 20)

	startTime = Date.now() - this.interval
	endTime = Date.now()
	minTime = Number.MAX_SAFE_INTEGER
	maxTime = 0
	visibleSeries: string[] = []

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
			grid: { left: "60", right: "20", top: "15" },
			autoResize: true,
			darkMode: true,
			xAxis: { type: "time" },
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
				appendTo: "html",
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
				show: true,
				bottom: 0,
				selected: { Cumulative: false },
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
			this.visibleSeries = this.chart
				.getOption()
				.series.filter((series: any) => params.selected[series.name])
				.map((item: any) => item.name)
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
		this.chart.setOption(
			{
				series: series,
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
		for (const groupHistory of groupedHistories) {
			if (this.visibleSeries.length !== 0 && !this.visibleSeries.includes(groupHistory.index.name!)) {
				continue
			}
			const preparedResults = this.prepareResults(this.getHistoryByView(groupHistory, view!), fieldName)
			series.push(this.createSeriesItem(groupHistory, preparedResults, fieldName, view!))
		}
		if (this.hasCumulative) {
			series.push(this.createCumulativeSeries(series, fieldName))
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
		return {
			type: "bar",
			stack: "total",
			color: groupedHistory.index.mainColor,
			name: this.fixedValueName || groupedHistory.index.name,
			data: preparedResults.data.map((history: any) => {
				return [new Date(this.getTimeByView(history, view)), (history[fieldName] as BigNumber).div(BigNumber(10).pow(this.decimals)).toNumber()]
			}),
			animation: true,
		}
	}

	private createCumulativeSeries(series: any[], fieldName: string) {
		// Start with the first series' data structure
		const baseData = series[0].data.map((item: any) => [item[0], 0])

		// Accumulate values across all series
		const cumulativeData = baseData.map((baseItem: [Date, number], index: number) => {
			const date = baseItem[0]
			let cumulativeValue = 0

			for (const serie of series) {
				if (serie.data[index]) {
					cumulativeValue += serie.data[index][1]
				}
			}

			return [date, cumulativeValue]
		})

		// Create a running total
		let runningTotal = 0
		const finalCumulativeData = cumulativeData.map(([date, value]: [Date, number]) => {
			runningTotal += value
			return [date, runningTotal]
		})

		return {
			type: "line",
			name: "Cumulative",
			color: "#00ffa2",
			data: finalCumulativeData,
			animation: true,
			smooth: true, // Optional: makes the line smoother
			lineStyle: {
				width: 2, // Optional: adjust line width as needed
			},
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

		if (!this.showPartyBVolume) {
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

		let content = `
      <div style="font-family: Arial, sans-serif; padding: 10px; border-radius: 5px; border: 0">
        <div style="font-size: 14px; color: #ffffff; margin-bottom: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.2); padding-bottom: 5px;">
          <strong>${dateString}</strong>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
    `

		let sum = 0

		params.forEach(item => {
			if (item.seriesName !== "Cumulative") {
				// Exclude Cumulative series from sum
				const color = item.color as string
				let value: number = 0
				if (Array.isArray(item.value) && item.value[1] != null) {
					value = Number(item.value[1])
				} else if (typeof item.value === "number") {
					value = item.value
				}
				sum += value

				content += `
                <tr>
                  <td style="padding: 3px 5px;">
                    <span style="display: inline-block; width: 10px; height: 10px; background-color: ${color}; border-radius: 50%; margin-right: 5px;"></span>
                    <span style="color: #cccccc;">${item.seriesName || "Unknown"}</span>
                  </td>
                  <td style="padding: 3px 5px; text-align: right; color: #ffffff; font-weight: bold;">
                    ${this.yAxisFormatter(value)}
                  </td>
                </tr>
            `
			}
		})

		// Add Cumulative series if it exists
		const cumulativeItem = params.find(item => item.seriesName === "Cumulative")
		if (cumulativeItem) {
			const color = cumulativeItem.color as string
			let value: number = 0
			if (Array.isArray(cumulativeItem.value) && cumulativeItem.value[1] != null) {
				value = Number(cumulativeItem.value[1])
			} else if (typeof cumulativeItem.value === "number") {
				value = cumulativeItem.value
			}

			content += `
            <tr>
              <td style="padding: 3px 5px;">
                <span style="display: inline-block; width: 10px; height: 10px; background-color: ${color}; border-radius: 50%; margin-right: 5px;"></span>
                <span style="color: #cccccc;">Cumulative</span>
              </td>
              <td style="padding: 3px 5px; text-align: right; color: #ffffff; font-weight: bold;">
                ${this.yAxisFormatter(value)}
              </td>
            </tr>
        `
		}

		// Add Aggregated row
		content += `
        <tr style="border-top: 1px solid rgba(255, 255, 255, 0.2);">
          <td style="padding: 5px; color: #cccccc;">
            <strong>Aggregated</strong>
          </td>
          <td style="padding: 5px; text-align: right; color: #ffffff; font-weight: bold;">
            ${this.yAxisFormatter(sum)}
          </td>
        </tr>
    `

		content += `
        </table>
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
}
