import {NgModule} from "@angular/core"
import {RouterModule, Routes} from "@angular/router"
import {HomeComponent} from "./home/home.component"
import {EnvironmentService} from "./services/enviroment.service"
import {PanelHomeComponent} from "./panel-home/panel-home.component"
import {LoginComponent} from "./login/login.component"
import {authGuard} from "./auth.guard"
import {QuoteLoaderComponent} from "./panel-home/quote-loader/quote-loader.component"
import {HedgerStateViewerComponent} from "./panel-home/hedger-state-viewer/hedger-state-viewer.component"

const routes: Routes = []


@NgModule({
	imports: [RouterModule.forRoot(routes)],
	exports: [RouterModule],
})
export class AppRoutingModule {
	constructor(environmentService: EnvironmentService) {
		if (environmentService.getValue("panel")) {
			routes.push(
				{
					path: "home",
					component: PanelHomeComponent,
					children: [
						{
							path: "tools/quote_loader",
							component: QuoteLoaderComponent,
						},
						{
							path: "hedger_stat/:name",
							component: HedgerStateViewerComponent,
							canActivate: [authGuard],
						},
					],
				},
			)
		} else {
			routes.push({
				path: "home",
				component: HomeComponent,
			})
		}
		routes.push({
			path: "login",
			component: LoginComponent,
		})
	}
}
