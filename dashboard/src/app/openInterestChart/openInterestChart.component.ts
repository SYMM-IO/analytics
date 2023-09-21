import {Component, Input, OnInit} from "@angular/core";
import BigNumber from "bignumber.js";
import {Observable, Subject} from "rxjs";
import {DailyHistory} from "../services/graph-models";

@Component({
	selector: "app-openInterestChart",
	templateUrl: "./openInterestChart.component.html",
	styleUrls: ["./openInterestChart.component.scss"],
})
export class OpenInterestChartComponent implements OnInit {
	loadedResults?: DailyHistory[];
	groupedByMonth: boolean = false;

	@Input() dailyHistories!: Observable<DailyHistory[]>;
	series: Subject<any> = new Subject<any>();

	ngOnInit(): void {
		this.dailyHistories.subscribe((results) => {
			this.loadedResults = results;
			this.updateChart(results);
		});
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
						acc[yearMonth] = {id: yearMonth + "_", openInterest: BigNumber(0)};
					}
					acc[yearMonth].openInterest = acc[yearMonth].openInterest.plus(
						curr.openInterest!
					);
					return acc;
				}, {})
			);
		let sum = BigNumber(0);
		let accumulatedData = data.map((dailyHistory) => ({...dailyHistory}));
		accumulatedData = accumulatedData.map((dailyHistory: DailyHistory) => {
			sum = sum.plus(dailyHistory.openInterest!);
			dailyHistory.openInterest = sum;
			return dailyHistory;
		});
		return {
			data: data,
			accumulatedData: accumulatedData,
		};
	}

	updateChart(results: DailyHistory[]) {
		let preparedResults = this.prepareResults(results);
		this.series.next([
			{
				type: "bar",
				name: "Open Interest",
				data: preparedResults.data.map((dailyHistory: DailyHistory) => [
					new Date(DailyHistory.getTime(dailyHistory)!),
					dailyHistory.openInterest!.div(BigNumber(10).pow(18)).toNumber(),
				]),
				animation: true,
			},
		])
	}

	onGroupByMonthChanged(groupBy: boolean) {
		this.groupedByMonth = groupBy;
		if (this.loadedResults)
			this.updateChart(this.loadedResults)
	}

	tooltipFormatter(x: any, y: number) {
		const timeLabel = x.toLocaleDateString();
		return timeLabel + "<br/>" + "Volume" + " : " + BigNumber(y).toFormat(3);
	}
}
