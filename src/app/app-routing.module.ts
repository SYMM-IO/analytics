import { TuiButtonLoading } from "@taiga-ui/kit"
import { NgModule } from "@angular/core"
import { RouterModule, Routes } from "@angular/router"
import { HomeComponent } from "./home/home.component"
import { EnvironmentService } from "./services/enviroment.service"
import { LoginComponent } from "./login/login.component"

const routes: Routes = []

@NgModule({
	imports: [RouterModule.forRoot(routes), TuiButtonLoading],
	exports: [RouterModule],
})
export class AppRoutingModule {
	constructor(environmentService: EnvironmentService) {
		routes.push({
			path: "home",
			component: HomeComponent,
		})
		routes.push({
			path: "login",
			component: LoginComponent,
		})
	}
}
