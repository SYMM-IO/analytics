import {Component, ElementRef, Input, OnDestroy, OnInit, ViewChild} from "@angular/core"
import {EChartsOption} from "echarts"
import {max, Observable} from "rxjs"
import {DailyHistory} from "../models"
import BigNumber from "bignumber.js"
import {aggregateDailyHistories} from "../utils"
import {StateService} from "../state.service"
import {AffiliateHistory} from "../affiliate.history"

@Component({
    selector: 'app-chart',
    templateUrl: './chart.component.html',
    styleUrls: ['./chart.component.scss'],
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

    interval = 30.44 * 6 * 24 * 60 * 60 * 1000 // six month
    startTime = Date.now() - this.interval
    endTime = Date.now()
    minTime: number = 1000000000000000
    maxTime: number = 0

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
    }

    ngOnDestroy() {
    }

    onChartInit(chart: any) {
        this.chart = chart
        this.dailyAffiliateHistories.subscribe((results) => {
            this.loadedResults = results
            this.updateChart(results, this.fieldName)
        })
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
        let i = 0
        let accumulatedData = []
        let prepared = []
        for (const affiliateHistory of affiliateHistories) {
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

    protected readonly max = max
}
