import {Component, ElementRef, EventEmitter, Input, OnDestroy, OnInit, Output, ViewChild} from "@angular/core";
import {EChartsOption} from "echarts";
import {Observable, Subscription} from "rxjs";
import {EnvironmentService} from "../services/enviroment.service";

@Component({
	selector: 'app-chart',
	templateUrl: './chart.component.html',
	styleUrls: ['./chart.component.scss']
})
export class ChartComponent implements OnInit, OnDestroy {
	chartOption?: EChartsOption;

	@ViewChild("chart") chartElement!: ElementRef;
	chart: any;
	subscription?: Subscription;

	@Input() series!: Observable<any>;
	@Input() chartTitle!: string;
	@Input() tooltipFormatter?: (x: any, y: any) => string;
	@Input() hasGroupByMonthAction!: boolean;
	@Output() groupByMonth = new EventEmitter<boolean>()

	groupedByMonth: boolean = false;
	mainColor: string;

	constructor(readonly environmentService: EnvironmentService) {
		this.mainColor = environmentService.getValue("mainColor");
	}

	ngOnInit(): void {
		this.chartOption = {
			backgroundColor: "transparent",
			color: [this.mainColor, '#3398DB', '#7CFC00', '#FF7F50', '#8B0000', '#D2691E'],
			grid: {
				left: "70",
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
				text: this.chartTitle,
				left: "left",
			},
			tooltip: {
				trigger: "axis",
				axisPointer: {
					type: "shadow",
				},
				formatter: this.tooltipFormatter != null ? (params: any) => {
					if (params != null && params[params.length - 1].data != null) {
						const p = params[params.length - 1].data;
						return this.tooltipFormatter!(p[0], p[1]);
					}
					return "";
				} : undefined,
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
							this.groupByMonth.next(this.groupedByMonth)
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

	ngOnDestroy() {
		this.subscription?.unsubscribe();
	}

	onChartInit(chart: any) {
		this.chart = chart;
		this.subscription = this.series.subscribe(
			value => {
				this.chart.setOption(
					{
						series: value,
					},
					false,
					false
				);
			}
		)
	}
}
