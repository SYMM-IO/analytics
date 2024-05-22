import {Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from "@angular/core"
import {EChartsOption} from "echarts"
import {merge, Observable} from "rxjs"
import {DailyHistory} from "../models"
import BigNumber from "bignumber.js"
import {aggregateDailyHistories} from "../utils"
import {StateService} from "../services/state.service"
import {AffiliateHistory} from "../affiliate.history"
import {tuiItemsHandlersProvider} from "@taiga-ui/kit";
import {FormControl} from "@angular/forms"
import {TuiDay} from "@taiga-ui/cdk";


const intervalOptionsStringify = (item: any): string => item.name;

@Component({
    selector: 'app-chart',
    templateUrl: './chart.component.html',
    styleUrls: ['./chart.component.scss'],
    providers: [tuiItemsHandlersProvider({stringify: intervalOptionsStringify})],
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

    loadedResults?: AffiliateHistory[]
    @Input() dailyAffiliateHistories!: Observable<AffiliateHistory[]>
    groupedByMonth: boolean = false


    intervalOptions: readonly any[] = [
        {days: 30, name: '1M'},
        {days: 90, name: '3M'},
        {days: 180, name: '6M'},
        {days: 365, name: '1Y'},
        {days: 0, name: 'Custom'},
    ];
    intervalOptionsStringify = intervalOptionsStringify
    intervalForm = new FormControl(this.intervalOptions[2])
    intervalRangeForm = new FormControl()
    readonly intervalRangeMin = new TuiDay(2000, 2, 20);
    readonly intervalRangeMax = new TuiDay(2040, 2, 20);

    startTime = Date.now() - this.interval
    endTime = Date.now()
    minTime: number = 1000000000000000
    maxTime: number = 0

    visibleSeries: any[] = []

    constructor(readonly stateService: StateService) {
    }

    ngOnInit(): void {
        let that = this
        this.chartOption = {
            backgroundColor: "transparent",
            color: ['#3398DB', '#7CFC00', '#FF7F50', '#8B0000', '#D2691E'],
            grid: {
                left: "60",
                right: "20",
                top: "15",
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
                show: false,
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
                        let p = params[params.length - 1].seriesName == "Cumulative" ? params.slice(0, params.length - 1) : params
                        let sum = p.reduce((a: any, b: any) => a + b.value[1], 0)
                        res += '<br/>' + `<span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:black"></span>`
                        res += "Aggregated" + ': ' + that.yAxisFormatter(sum) + '<br/>'
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
                show: false,
            },
            dataZoom: [
                {
                    type: "inside",
                    throttle: 50,
                },
            ],
        }
        merge(this.intervalForm.valueChanges, this.intervalRangeForm.valueChanges).subscribe(value => {
            if (this.updateRange() && this.loadedResults != null)
                this.updateChart(this.loadedResults, this.fieldName)
        });
    }

    ngOnDestroy() {
    }

    onChartInit(chart: any) {
        this.chart = chart
        this.dailyAffiliateHistories.subscribe((results) => {
            this.loadedResults = results
            this.updateChart(results, this.fieldName)
        })
        this.chart.on('legendselectchanged', (params: any) => {
            this.visibleSeries = this.chart.getOption().series.filter((series: any) => params.selected[series.name]).map((item: any) => item.name)
            if (this.loadedResults)
                this.updateChart(this.loadedResults, this.fieldName)
        });
    }

    onGroupByMonthChanged() {
        this.groupedByMonth = !this.groupedByMonth
        if (this.loadedResults)
            this.updateChart(this.loadedResults, this.fieldName)
    }


    prepareResults(results: DailyHistory[], fieldName: string) {
        let data = results.filter(dh => {
            let time = DailyHistory.getTime(dh)!
            this.minTime = Math.min(this.minTime, time)
            this.maxTime = Math.max(this.maxTime, time)
            return time > this.startTime && time <= this.endTime
        }).map((dailyHistory) => ({...dailyHistory}))
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
                        curr[fieldName]!,
                    )
                    return acc
                }, {}),
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

    updateChart(affiliateHistories: AffiliateHistory[], fieldName: string) {
        let series = []
        let accumulatedData = []
        let prepared = []
        for (const affiliateHistory of affiliateHistories) {
            if (this.visibleSeries.length != 0 && !this.visibleSeries.includes(affiliateHistory.affiliate.name))
                continue
            let preparedResults = this.prepareResults(affiliateHistory.histories, fieldName)
            prepared.push(preparedResults)
            series.push({
                type: "bar",
                stack: 'total',
                color: affiliateHistory.affiliate.mainColor,
                name: this.fixedValueName ? this.fixedValueName : affiliateHistory.affiliate.name,
                data: preparedResults.data.map((dailyHistory: DailyHistory) => [
                    new Date(DailyHistory.getTime(dailyHistory)!),
                    (dailyHistory[fieldName]! as BigNumber).div(BigNumber(10).pow(this.decimals)).toNumber(),
                ]),
                animation: true,
            })
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
                    ],
                ),
                animation: true,
            })
        }
        this.chart.setOption(
            {
                series: series,
            },
            false,
            false,
        )
    }

    get interval(): number {
        if (!this.intervalForm)
            return 0
        const optionValue = this.intervalForm.value.days
        if (optionValue > 0) {
            return optionValue * 24 * 60 * 60 * 1000
        } else {
            return this.intervalRangeForm.value
        }
    }

    updateRange(): boolean {
        const optionValue = this.intervalForm.value.days
        if (optionValue > 0) {
            this.endTime = Date.now()
            this.startTime = this.endTime - this.interval
            return true
        } else {
            if (this.intervalRangeForm.value) {
                this.endTime = (this.intervalRangeForm.value.to as TuiDay).toUtcNativeDate().getTime() + 1
                this.startTime = (this.intervalRangeForm.value.from as TuiDay).toUtcNativeDate().getTime() - 1
                return true
            }
        }
        return false
    }

    goBack() {
        this.endTime = this.startTime
        this.startTime = this.startTime - this.interval
        if (this.loadedResults)
            this.updateChart(this.loadedResults, this.fieldName)
    }

    goForward() {
        this.startTime = this.endTime
        this.endTime = this.endTime + this.interval
        if (this.loadedResults)
            this.updateChart(this.loadedResults, this.fieldName)
    }

    onResize(event: DOMRectReadOnly) {
        if (this.chart)
            this.chart.resize({
                width: event.width - 15,
                height: event.height,
            })
    }
}
