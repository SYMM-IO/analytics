import {TuiButtonLoading} from "@taiga-ui/kit";
import {NgModule} from "@angular/core"
import {RouterModule, Routes} from "@angular/router"
import {HomeComponent} from "./home/home.component"
import {EnvironmentService} from "./services/enviroment.service"
import {PanelHomeComponent} from "./panel-home/panel-home.component"
import {LoginComponent} from "./login/login.component"
import {QuoteLoaderComponent} from "./panel-home/quote-loader/quote-loader.component"

const routes: Routes = []


@NgModule({
	imports: [RouterModule.forRoot(routes), TuiButtonLoading],
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
