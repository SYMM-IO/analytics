import {NgModule} from "@angular/core";
import {BrowserModule} from "@angular/platform-browser";

import {HttpClientModule} from "@angular/common/http";
import {BrowserAnimationsModule} from "@angular/platform-browser/animations";
import {InMemoryCache} from "@apollo/client/core";
import {Apollo, APOLLO_OPTIONS} from "apollo-angular";
import {HttpLink} from "apollo-angular/http";
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
import {OpenInterestChartComponent} from "./openInterestChart/openInterestChart.component";
import {PlatformFeeChartComponent} from "./platformFeeChart/platformFeeChart.component";
import {QuotesCountChartComponent} from "./quotesCountChart/quotesCountChart.component";
import {GraphQlClient} from "./services/graphql-client";
import {TradeVolumeChartComponent} from "./tradeVolumeChart/tradeVolumeChart.component";
import {ActiveUsersChartComponent} from "./activeUsersChart/activeUsersChart.component";
import {NewUsersChartComponent} from "./newUsersChart/newUsersChart.component";
import {ENVIRONMENT} from "./services/enviroment.service";
import {environment} from "../environments/environment";

@NgModule({
    declarations: [
        AppComponent,
        QuotesCountChartComponent,
        HomeComponent,
        TradeVolumeChartComponent,
        InfoComponent,
        PlatformFeeChartComponent,
        OpenInterestChartComponent,
        ActiveUsersChartComponent,
        NewUsersChartComponent
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
        {
            provide: APOLLO_OPTIONS,
            useFactory(httpLink: HttpLink) {
                return {
                    cache: new InMemoryCache(),
                    link: httpLink.create({
                        uri: environment.subgraphUrl,
                    }),
                };
            },
            deps: [HttpLink],
        },
        GraphQlClient,
        Apollo,
        MessageService,
    ],
    bootstrap: [AppComponent],
})
export class AppModule {
}
