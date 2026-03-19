/**
 * Custom ECharts bundle — only the modules we use.
 * Reduces JS payload from ~1MB to ~300KB.
 */
import * as echarts from "echarts/core"
import { BarChart } from "echarts/charts"
import {
	TooltipComponent,
	GridComponent,
	LegendComponent,
	DataZoomComponent,
	TitleComponent,
	ToolboxComponent,
} from "echarts/components"
import { CanvasRenderer } from "echarts/renderers"

echarts.use([BarChart, TooltipComponent, GridComponent, LegendComponent, DataZoomComponent, TitleComponent, ToolboxComponent, CanvasRenderer])

// ngx-echarts destructures { init } from the resolved module
export const init = echarts.init
