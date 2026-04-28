import { ChangeDetectionStrategy, Component, Input } from "@angular/core"

let nextId = 0

@Component({
	selector: "app-sparkline",
	templateUrl: "./sparkline.component.html",
	styleUrls: ["./sparkline.component.scss"],
	changeDetection: ChangeDetectionStrategy.OnPush,
	standalone: false,
})
export class SparklineComponent {
	readonly uid = `spark-${nextId++}`
	readonly width = 600
	readonly height = 120

	@Input() color = "#FF7A6E"

	@Input() set data(value: number[] | null | undefined) {
		const series = (value ?? []).filter(v => Number.isFinite(v))
		this._data = series
		const { line, area } = this.buildPaths(series)
		this.linePath = line
		this.areaPath = area
	}
	get data(): number[] {
		return this._data
	}
	private _data: number[] = []

	linePath = ""
	areaPath = ""

	private buildPaths(values: number[]): { line: string; area: string } {
		if (values.length < 2) return { line: "", area: "" }
		const w = this.width
		const h = this.height
		const min = Math.min(...values)
		const max = Math.max(...values)
		const range = max - min || 1
		const padY = 4
		const usableH = h - padY * 2
		const stepX = w / (values.length - 1)
		const points = values.map((v, i) => {
			const x = i * stepX
			const y = h - padY - ((v - min) / range) * usableH
			return [x, y] as const
		})
		// Catmull-Rom-ish smoothing via cubic bezier control points.
		let line = `M ${points[0][0].toFixed(2)} ${points[0][1].toFixed(2)}`
		for (let i = 0; i < points.length - 1; i++) {
			const [x0, y0] = points[Math.max(0, i - 1)]
			const [x1, y1] = points[i]
			const [x2, y2] = points[i + 1]
			const [x3, y3] = points[Math.min(points.length - 1, i + 2)]
			const t = 0.18
			const cp1x = x1 + (x2 - x0) * t
			const cp1y = y1 + (y2 - y0) * t
			const cp2x = x2 - (x3 - x1) * t
			const cp2y = y2 - (y3 - y1) * t
			line += ` C ${cp1x.toFixed(2)} ${cp1y.toFixed(2)}, ${cp2x.toFixed(2)} ${cp2y.toFixed(2)}, ${x2.toFixed(2)} ${y2.toFixed(2)}`
		}
		const area = `${line} L ${w} ${h} L 0 ${h} Z`
		return { line, area }
	}
}
