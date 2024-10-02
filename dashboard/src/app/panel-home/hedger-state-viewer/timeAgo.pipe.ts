import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
	name: 'timeAgo',
})
export class TimeAgoPipe implements PipeTransform {

	transform(value: string | undefined): string {
		if (!value)
			return "";
		const secondsPerMinute = 60;
		const secondsPerHour = 3600;
		const secondsPerDay = 86400;
		const secondsPerMonth = 2592000;
		const secondsPerYear = 31536000;

		// Convert the input UTC date string to a Date object
		const utcDate = new Date(value);

		// Convert the UTC date to local time
		const localDate = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000);

		const now = new Date();
		const elapsedSeconds = Math.round((now.getTime() - localDate.getTime()) / 1000);

		if (elapsedSeconds < secondsPerMinute) {
			return `${elapsedSeconds} seconds ago`;
		} else if (elapsedSeconds < secondsPerHour) {
			return `${Math.round(elapsedSeconds / secondsPerMinute)} minutes ago`;
		} else if (elapsedSeconds < secondsPerDay) {
			return `${Math.round(elapsedSeconds / secondsPerHour)} hours ago`;
		} else if (elapsedSeconds < secondsPerMonth) {
			return `${Math.round(elapsedSeconds / secondsPerDay)} days ago`;
		} else if (elapsedSeconds < secondsPerYear) {
			return `${Math.round(elapsedSeconds / secondsPerMonth)} months ago`;
		} else {
			return `${Math.round(elapsedSeconds / secondsPerYear)} years ago`;
		}
	}

}
