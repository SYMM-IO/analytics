import {Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from "@angular/core"
import {EChartsOption} from "echarts"
import {Observable} from "rxjs"
import {EnvironmentService} from "../services/enviroment.service"
import {DailyHistory} from "../services/graph-models"
import BigNumber from "bignumber.js"
import {aggregateDailyHistories} from "../utils"
import {SubEnvironmentInterface} from "../../environments/environment-interface"
import {StateService} from "../state.service"

@Component({
	selector: 'app-chart',
	templateUrl: './chart.component.html',
	styleUrls: ['./chart.component.scss']
})
export class ChartComponent implements OnInit, OnDestroy {
	chartOption?: EChartsOption

	@ViewChild("chart") chartElement!: ElementRef
	chart: any

	@Input() fieldName!: string
	@Input() fixedValueName?: string
	@Input() decimals: number = 0
	@Input() chartTitle!: string
	@Input() yAxisFormatter: (x: any) => string = (a) => a
	@Input() tooltipFormatter?: any
	@Input() hasGroupByMonthAction!: boolean
	@Input() hasCumulative: boolean = true

	loadedResults?: DailyHistory[][]
	@Input() dailyHistories!: Observable<DailyHistory[][]>

	environments: SubEnvironmentInterface[]

	groupedByMonth: boolean = false
	mainColor: string

	constructor(readonly environmentService: EnvironmentService, readonly stateService: StateService) {
		this.mainColor = environmentService.getValue("mainColor")
		this.environments = environmentService.getValue("environments")
	}

	ngOnInit(): void {
		let that = this
		this.chartOption = {
			backgroundColor: "transparent",
			color: [this.mainColor, '#3398DB', '#7CFC00', '#FF7F50', '#8B0000', '#D2691E'],
			grid: {
				left: "60",
				right: "20",
			},
			autoResize: true,
			darkMode: true,
			xAxis: {
				type: "time",
			},
			yAxis: {
				type: "value",
				splitNumber: 4,
				axisLabel: {
					formatter: (value: any) => {
						if (value >= 1000000000) {
							return (value / 1000000000).toFixed(2) + "B"
						} else if (value >= 1000000) {
							return (value / 1000000).toFixed(2) + "M"
						} else if (value >= 1000) {
							return (value / 1000).toFixed(2) + "K"
						}
						return value
					},
				},
			},
			title: {
				text: this.chartTitle,
				left: "left",
			},
			tooltip: {
				trigger: "axis",
				axisPointer: {
					type: "line",
				},
				formatter: (params: any) => {
					let date = params[0].data[0].toLocaleDateString()
					let res = `Date: <b>${date}</b> <br/>`
					params.forEach(function (item: any) {
						res += `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${item.color}"></span>`
						res += item.seriesName + ': ' + that.yAxisFormatter(item.value[1]) + '<br/>'
					})
					if (params.length > 1) {
						let sum = params.reduce((a: any, b: any) => a + b.value[1], 0)
						res += '<br/>' + `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:black"></span>`
						res +=  "Aggregated" + ': ' + that.yAxisFormatter(sum) + '<br/>'
					}
					return res
				},
			},
			legend: {
				show: true,
				bottom: 0,
				selected: {
					Cumulative: false,
				},
			},
			toolbox: {
				show: true,
				orient: "horizontal",
				top: "start",
				feature: {
					myGroupByMonthAction: {
						show: this.hasGroupByMonthAction,
						title: "Group by Month",
						icon: "path://M10,90 L25,20 L42,75 L59,20 L74,90",
						onclick: (params: any) => {
							this.groupedByMonth = !this.groupedByMonth
							this.onGroupByMonthChanged()
							this.chart.setOption(
								{
									toolbox: {
										feature: {
											myGroupByMonthAction: {
												iconStyle: {
													normal: {
														borderColor: this.groupedByMonth
															? "#3C92BD"
															: "#9595A6",
													},
												},
											},
										},
									},
								},
								false,
								false
							)
						},
					},
					saveAsImage: {
						show: true,
					},
				},
			},
			dataZoom: [
				{
					type: "inside",
					throttle: 50,
				},
			],
		}
	}

	ngOnDestroy() {
	}

	onChartInit(chart: any) {
		this.chart = chart
		this.dailyHistories.subscribe((results) => {
			this.loadedResults = results
			this.updateChart(results, this.fieldName)
		})
	}

	onGroupByMonthChanged() {
		if (this.loadedResults)
			this.updateChart(this.loadedResults, this.fieldName)
	}


	prepareResults(results: DailyHistory[], fieldName: string) {
		let data = results.map((dailyHistory) => ({...dailyHistory}))
		if (this.groupedByMonth)
			data = Object.values(
				data.reduce((acc: any, curr: DailyHistory) => {
					const date = new Date(DailyHistory.getTime(curr)!)
					const year = date.getFullYear()
					const month = date.getMonth()
					const yearMonth = new Date(year, month, 1, 0, 0, 0, 0).getTime()
					if (!acc[yearMonth]) {
						acc[yearMonth] = {id: yearMonth + "_"}
						acc[yearMonth][fieldName] = BigNumber(0)
					}
					acc[yearMonth][fieldName] = acc[yearMonth][fieldName].plus(
						curr[fieldName]!
					)
					return acc
				}, {})
			)
		let sum = BigNumber(0)
		let accumulatedData = data.map((dailyHistory) => ({...dailyHistory}))
		accumulatedData = accumulatedData.map((dailyHistory: DailyHistory) => {
			sum = sum.plus(dailyHistory[fieldName]!)
			dailyHistory[fieldName] = sum
			return dailyHistory
		})
		return {
			data: data,
			accumulatedData: accumulatedData,
		}
	}

	updateChart(results: DailyHistory[][], fieldName: string) {
		let series = []
		let i = 0
		let accumulatedData = []
		let prepared = []
		for (const result of results) {
			let preparedResults = this.prepareResults(result, fieldName)
			prepared.push(preparedResults)
			series.push({
				type: "bar",
				stack: 'total',
				color: this.environments[i].mainColor,
				name: this.fixedValueName ? this.fixedValueName : this.environments[i].name,
				data: preparedResults.data.map((dailyHistory: DailyHistory) => [
					new Date(DailyHistory.getTime(dailyHistory)!),
					(dailyHistory[fieldName]! as BigNumber).div(BigNumber(10).pow(this.decimals)).toNumber(),
				]),
				animation: true,
			})
			i += 1
		}
		for (let j = 0; j < prepared[0].data.length; j++)
			accumulatedData.push(aggregateDailyHistories(prepared.map(ls => ls.accumulatedData[j])))

		if (this.hasCumulative) {
			series.push({
				type: "line",
				name: "Cumulative",
				color: "#00ffa2",
				data: accumulatedData.map(
					(dailyHistory: DailyHistory) => [
						new Date(DailyHistory.getTime(dailyHistory)!),
						(dailyHistory[fieldName]! as BigNumber).div(BigNumber(10).pow(this.decimals)).toNumber(),
					]
				),
				animation: true,
			})
		}
		this.chart.setOption(
			{
				series: series,
			},
			false,
			false
		)
	}

	onResize(event: DOMRectReadOnly) {
		if (this.chart)
			this.chart.resize({
				width: event.width - 15,
				height: event.height
			})
	}
}
