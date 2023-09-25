import {Component} from "@angular/core";
import {Router} from "@angular/router";
import {MenuItem, PrimeIcons, PrimeNGConfig} from "primeng/api";
import {EnvironmentService} from "./services/enviroment.service";

@Component({
    selector: "app-root",
    templateUrl: "./app.component.html",
    styleUrls: ["./app.component.scss"],
})
export class AppComponent {
    title = "symmio-analytics-dashboard";
    display: boolean = false;
    items: MenuItem[];
    readonly assetsFolder: string;
    readonly mainColor: string;
    readonly aggregated: boolean;

    constructor(
        private primengConfig: PrimeNGConfig,
        private readonly router: Router,
        readonly environmentService: EnvironmentService
    ) {
        this.items = [
            {label: "Home", icon: PrimeIcons.HOME, routerLink: ["/home"]},
        ];
        this.assetsFolder = environmentService.getValue("assetsFolder");
        this.mainColor = environmentService.getValue("mainColor");
        this.aggregated = environmentService.getValue("aggregate");
        let favIcon: HTMLLinkElement = document.querySelector('#favIcon')!;
        favIcon.href = `assets/${this.assetsFolder}/favicon.ico`;
    }

    ngOnInit() {
        this.primengConfig.ripple = true;
        this.router.navigate(["/home"]);
    }
}
