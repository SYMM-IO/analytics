import {NgModule} from "@angular/core";
import {BrowserModule} from "@angular/platform-browser";

import {HttpClientModule} from "@angular/common/http";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";
import {Apollo} from "apollo-angular";
import {NgxEchartsModule} from "ngx-echarts";
import {MessageService} from "primeng/api";
import {ButtonModule} from "primeng/button";
import {MenuModule} from "primeng/menu";
import {SidebarModule} from "primeng/sidebar";
import {SkeletonModule} from "primeng/skeleton";
import {ToastModule} from "primeng/toast";
import {ToolbarModule} from "primeng/toolbar";
import {AppRoutingModule} from "./app-routing.module";
import {AppComponent} from "./app.component";
import {HomeComponent} from "./home/home.component";
import {InfoComponent} from "./info/info.component";
import {ENVIRONMENT} from "./services/enviroment.service";
import {environment} from "../environments/environment";
import {ChartComponent} from './chart/chart.component';
import {AggregateHomeComponent} from './aggregate-home/aggregate-home.component';

@NgModule({
	declarations: [
		AppComponent,
		HomeComponent,
		InfoComponent,
		ChartComponent,
		AggregateHomeComponent
	],
	imports: [
		BrowserModule,
		BrowserAnimationsModule,
		AppRoutingModule,
		ToolbarModule,
		ButtonModule,
		SidebarModule,
		MenuModule,
		HttpClientModule,
		NgxEchartsModule.forRoot({
			echarts: () => import("echarts"),
		}),
		SkeletonModule,
		ToastModule,
	],
	providers: [
		{provide: ENVIRONMENT, useValue: environment},
		Apollo,
		MessageService,
	],
	bootstrap: [AppComponent],
})
export class AppModule {
}
