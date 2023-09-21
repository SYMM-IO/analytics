import {Component, Input, OnInit} from "@angular/core";
import BigNumber from "bignumber.js";
import {Observable, Subject} from "rxjs";
import {DailyHistory} from "../services/graph-models";

@Component({
	selector: "app-newUsersChart",
	templateUrl: "./newUsersChart.component.html",
	styleUrls: ["./newUsersChart.component.scss"],
})
export class NewUsersChartComponent implements OnInit {
	loadedResults?: DailyHistory[];
	groupedByMonth: boolean = false;
	@Input() dailyHistories!: Observable<DailyHistory[]>;

	series: Subject<any> = new Subject<any>();

	constructor() {
	}

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
						acc[yearMonth] = {id: yearMonth + "_", newUsers: BigNumber(0)};
					}
					acc[yearMonth].newUsers = acc[yearMonth].newUsers.plus(
						curr.newUsers!
					);
					return acc;
				}, {})
			);
		let sum = BigNumber(0);
		let accumulatedData = data.map((dailyHistory) => ({...dailyHistory}));
		accumulatedData = accumulatedData.map((dailyHistory: DailyHistory) => {
			sum = sum.plus(dailyHistory.newUsers!);
			dailyHistory.newUsers = sum;
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
				name: "New Users",
				data: preparedResults.data.map((dailyHistory: DailyHistory) => [
					new Date(DailyHistory.getTime(dailyHistory)!),
					dailyHistory.newUsers!.toNumber(),
				]),
				animation: true,
			},
			{
				type: "line",
				name: "Cumulative",
				data: preparedResults.accumulatedData.map(
					(dailyHistory: DailyHistory) => [
						new Date(DailyHistory.getTime(dailyHistory)!),
						dailyHistory.newUsers!.toNumber(),
					]
				),
				animation: true,
			},
		]);
	}

	onGroupByMonthChanged(groupBy: boolean) {
		this.groupedByMonth = groupBy;
		if (this.loadedResults)
			this.updateChart(this.loadedResults)
	}

	tooltipFormatter(x: any, y: number) {
		const timeLabel = x.toLocaleDateString();
		return timeLabel + "<br/>" + "Count" + " : " + BigNumber(y).toFormat(0);
	}
}
