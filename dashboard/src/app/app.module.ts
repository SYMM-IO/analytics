import {TuiLet} from "@taiga-ui/cdk";
import {TuiCardLarge} from '@taiga-ui/layout';
import {
	TuiComboBoxModule,
	TuiInputDateRangeModule,
	TuiInputNumberModule,
	TuiSelectModule,
	TuiTextfieldControllerModule,
	TuiUnfinishedValidator
} from "@taiga-ui/legacy";
import {NG_EVENT_PLUGINS} from "@taiga-ui/event-plugins";
import {
	TuiAlert,
	TuiButton,
	TuiDataList,
	TuiDialog,
	TuiDropdown,
	TuiGroup,
	TuiHint,
	TuiIcon,
	TuiRoot,
	TuiSurface, TuiTitle
} from "@taiga-ui/core"
import {NgModule} from "@angular/core"
import {BrowserModule} from "@angular/platform-browser"

import {provideHttpClient, withInterceptors} from "@angular/common/http"
import {BrowserAnimationsModule} from "@angular/platform-browser/animations"
import {Apollo} from "apollo-angular"
import {NgxEchartsModule} from "ngx-echarts"
import {AppRoutingModule} from "./app-routing.module"
import {AppComponent} from "./app.component"
import {InfoComponent} from "./info/info.component"
import {ENVIRONMENT} from "./services/enviroment.service"
import {environment} from "../environments/environment"
import {ChartComponent} from './chart/chart.component'
import {HomeComponent} from './home/home.component'
import {ResizeObserverDirective} from './resize-observer.directive'
import {TuiAccordion, TuiBlock, TuiButtonLoading, TuiDataListWrapper, TuiRadio} from "@taiga-ui/kit"
import {PanelHomeComponent} from "./panel-home/panel-home.component"
import {ReactiveFormsModule} from "@angular/forms"
import {NgxJsonViewerModule} from "ngx-json-viewer"
import {httpInterceptor} from "./http.Interceptor"
import {BigNumberFormatPipe} from "./big-number-format.pipe"
import {QuoteLoaderComponent} from "./panel-home/quote-loader/quote-loader.component"
import {HedgerStateViewerComponent} from "./panel-home/hedger-state-viewer/hedger-state-viewer.component"
import {AffiliateStateViewerComponent} from "./panel-home/affiliate-state-viewer/affiliate-state-viewer.component"
import {TimeAgoPipe} from "./panel-home/hedger-state-viewer/timeAgo.pipe"

@NgModule({
	declarations: [
		AppComponent,
		InfoComponent,
		ChartComponent,
		HomeComponent,
		ResizeObserverDirective,
		PanelHomeComponent,
		BigNumberFormatPipe,
		QuoteLoaderComponent,
		HedgerStateViewerComponent,
		AffiliateStateViewerComponent,
		TimeAgoPipe,
		ChartComponent,
	],
	imports: [
		BrowserModule,
		BrowserAnimationsModule,
		AppRoutingModule,
		NgxEchartsModule.forRoot({
			echarts: () => import("echarts"),
		}),
		TuiRoot,
		TuiDialog,
		TuiAlert,
		TuiLet,
		TuiInputNumberModule,
		ReactiveFormsModule,
		TuiTextfieldControllerModule,
		TuiButton,
		TuiGroup,
		TuiBlock, ...TuiRadio,
		NgxJsonViewerModule,
		...TuiHint,
		...TuiAccordion,
		...TuiDropdown,
		...TuiDataList,
		TuiIcon,
		TuiSelectModule,
		...TuiDataListWrapper,
		TuiComboBoxModule,
		TuiInputDateRangeModule, TuiButtonLoading, TuiUnfinishedValidator,
		TuiCardLarge, TuiSurface, TuiTitle,
	],
	providers: [
		provideHttpClient(
			withInterceptors([httpInterceptor]),
		),
		{provide: ENVIRONMENT, useValue: environment},
		Apollo,
		NG_EVENT_PLUGINS
	],
	bootstrap: [AppComponent],
})
export class AppModule {
}
