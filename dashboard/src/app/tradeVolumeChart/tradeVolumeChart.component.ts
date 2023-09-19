import {Component, ElementRef, Input, OnInit, ViewChild} from "@angular/core";
import BigNumber from "bignumber.js";
import {EChartsOption} from "echarts";
import {Observable} from "rxjs";
import {DailyHistory} from "../services/graph-models";
import {EnvironmentService} from "../services/enviroment.service";

@Component({
	selector: "app-tradeVolumeChart",
	templateUrl: "./tradeVolumeChart.component.html",
	styleUrls: ["./tradeVolumeChart.component.scss"],
})
export class TradeVolumeChartComponent implements OnInit {
	chartOption: EChartsOption;

	@ViewChild("chart") chartElement!: ElementRef;
	chart: any;
	loadedResults?: DailyHistory[];
	accumulated: boolean = false;
	groupedByMonth: boolean = false;

	@Input() dailyHistories!: Observable<DailyHistory[]>;

	constructor(readonly environmentService: EnvironmentService) {
		let mainColor = environmentService.getValue("mainColor");
		this.chartOption = {
			backgroundColor: "transparent",
			color: [mainColor, '#3398DB', '#7CFC00', '#FF7F50', '#8B0000', '#D2691E'],
			grid: {
				left: "85",
				right: "50",
				height: "70%",
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
							return (value / 1000000000).toFixed(2) + "B";
						} else if (value >= 1000000) {
							return (value / 1000000).toFixed(2) + "M";
						} else if (value >= 1000) {
							return (value / 1000).toFixed(2) + "K";
						}
						return value;
					},
				},
			},
			title: {
				text: "Trade Volume",
				left: "left",
			},
			tooltip: {
				trigger: "axis",
				axisPointer: {
					type: "shadow",
				},
				formatter: (params: any) => {
					if (params != null && params[params.length - 1].data != null) {
						const p = params[params.length - 1].data;
						return this.tooltipFormatter(p[0], p[1]);
					}
					return "";
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
						show: true,
						title: "Group by Month",
						icon: "path://M10,90 L25,20 L42,75 L59,20 L74,90",
						onclick: (params: any) => {
							if (this.loadedResults == null) return;
							if (!this.groupedByMonth) {
								this.groupedByMonth = true;
								this.updateChart(this.loadedResults);
							} else {
								this.groupedByMonth = false;
								this.updateChart(this.loadedResults);
							}
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
							);
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
		};
	}

	ngOnInit(): void {
	}

	prepareResults(results: DailyHistory[]) {
		let data = results.map((dailyHistory) => ({...dailyHistory}));
		if (this.groupedByMonth)
			data = Object.values(
				data.reduce((acc: any, curr: DailyHistory) => {
					const date = new Date(DailyHistory.getTime(curr)!);
					const year = date.getFullYear();
					const month = date.getMonth();
					const yearMonth = new Date(year, month, 1, 0, 0, 0, 0).getTime();
					if (!acc[yearMonth]) {
						acc[yearMonth] = {id: yearMonth + "_", tradeVolume: BigNumber(0)};
					}
					acc[yearMonth].tradeVolume = acc[yearMonth].tradeVolume.plus(
						curr.tradeVolume!
					);
					return acc;
				}, {})
			);
		let sum = BigNumber(0);
		let accumulatedData = data.map((dailyHistory) => ({...dailyHistory}));
		accumulatedData = accumulatedData.map((dailyHistory: DailyHistory) => {
			sum = sum.plus(dailyHistory.tradeVolume!);
			dailyHistory.tradeVolume = sum;
			return dailyHistory;
		});
		return {
			data: data,
			accumulatedData: accumulatedData,
		};
	}

	updateChart(results: DailyHistory[]) {
		let preparedResults = this.prepareResults(results);
		const currentType = this.chart.getOption().series[0]?.type;
		this.chart.setOption(
			{
				series: [
					{
						type: currentType ? currentType : "bar",
						name: "Trading Volume",
						data: preparedResults.data.map((dailyHistory: DailyHistory) => [
							new Date(DailyHistory.getTime(dailyHistory)!),
							dailyHistory.tradeVolume!.div(BigNumber(10).pow(18)).toNumber(),
						]),
						animation: true,
					},
					{
						type: "line",
						name: "Cumulative",
						data: preparedResults.accumulatedData.map(
							(dailyHistory: DailyHistory) => [
								new Date(DailyHistory.getTime(dailyHistory)!),
								dailyHistory.tradeVolume!.div(BigNumber(10).pow(18)).toNumber(),
							]
						),

						animation: true,
					},
				],
			},
			false,
			false
		);
	}

	onChartInit(chart: any) {
		this.chart = chart;
		this.dailyHistories.subscribe((results) => {
			this.loadedResults = results;
			this.updateChart(results);
		});
	}

	tooltipFormatter(x: any, y: number) {
		const time = x;
		const timeLabel = time.toLocaleDateString();
		return timeLabel + "<br/>" + "Volume" + " : " + BigNumber(y).toFormat(3);
	}
}
