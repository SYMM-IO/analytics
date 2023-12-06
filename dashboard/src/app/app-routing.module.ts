import {NgModule} from "@angular/core"
import {RouterModule, Routes} from "@angular/router"
import {AggregateHomeComponent} from "./aggregate-home/aggregate-home.component"
import {EnvironmentService} from "./services/enviroment.service"
import {HomeComponent} from "./home/home.component"
import {PanelHomeComponent} from "./panel-home/panel-home.component"

const routes: Routes = []


@NgModule({
    imports: [RouterModule.forRoot(routes)],
    exports: [RouterModule],
})
export class AppRoutingModule {
    constructor(environmentService: EnvironmentService) {
        if (environmentService.getValue("panel")) {
            routes.push({
                path: "home",
                component: PanelHomeComponent,
            })
        } else if (environmentService.getValue("aggregate")) {
            routes.push({
                path: "home",
                component: AggregateHomeComponent,
            })
        } else {
            routes.push({
                path: "home",
                component: HomeComponent,
            })
        }
    }
}
