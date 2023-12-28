import {HttpInterceptorFn} from '@angular/common/http'
import {LoadingService} from "./services/Loading.service"
import {inject} from "@angular/core"
import {finalize} from "rxjs"
import {AuthService} from "./auth.service"
import {EnvironmentService} from "./services/enviroment.service"

export const httpInterceptor: HttpInterceptorFn = (req, next) => {
    let loadingService = inject(LoadingService)
    let authService = inject(AuthService)
    let environmentService = inject(EnvironmentService)
    loadingService.setLoading(true)
    if (req.url.indexOf(environmentService.getValue("serverUrl")) >= 0)
        req = req.clone({
            headers: req.headers.set('Authorization', `Bearer ${authService.getAuthToken()}`),
        })
    return next(req)
        .pipe(
            finalize(() => {
                loadingService.setLoading(false)
            }),
        )
}
