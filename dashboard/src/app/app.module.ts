import {NgDompurifySanitizer} from "@tinkoff/ng-dompurify"
import {
    TUI_SANITIZER,
    TuiAlertModule,
    TuiButtonModule,
    TuiDialogModule,
    TuiGroupModule,
    TuiHintModule,
    TuiModeModule,
    TuiRootModule,
    TuiTextfieldControllerModule,
    TuiThemeNightModule,
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
import {TuiLetModule} from "@taiga-ui/cdk"
import {ResizeObserverDirective} from './resize-observer.directive'
import {TuiInputNumberModule, TuiIslandModule, TuiRadioBlockModule} from "@taiga-ui/kit"
import {PanelHomeComponent} from "./panel-home/panel-home.component"
import {ReactiveFormsModule} from "@angular/forms"
import {NgxJsonViewerModule} from "ngx-json-viewer"
import {httpInterceptor} from "./http.Interceptor"
import {BigNumberFormatPipe} from "./big-number-format.pipe"

@NgModule({
    declarations: [
        AppComponent,
        InfoComponent,
        ChartComponent,
        HomeComponent,
        ResizeObserverDirective,
        PanelHomeComponent,
        BigNumberFormatPipe
    ],
    imports: [
        BrowserModule,
        BrowserAnimationsModule,
        AppRoutingModule,
        NgxEchartsModule.forRoot({
            echarts: () => import("echarts"),
        }),
        TuiRootModule,
        TuiDialogModule,
        TuiAlertModule,
        TuiThemeNightModule,
        TuiModeModule,
        TuiLetModule,
        TuiIslandModule,
        TuiInputNumberModule,
        ReactiveFormsModule,
        TuiTextfieldControllerModule,
        TuiButtonModule,
        TuiGroupModule,
        TuiRadioBlockModule,
        NgxJsonViewerModule,
        TuiHintModule,
    ],
    providers: [
        provideHttpClient(
            withInterceptors([httpInterceptor]),
        ),
        {provide: ENVIRONMENT, useValue: environment},
        Apollo,
        {provide: TUI_SANITIZER, useClass: NgDompurifySanitizer},
    ],
    bootstrap: [AppComponent],
})
export class AppModule {
}
