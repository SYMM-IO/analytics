import {CanActivateFn, Router} from '@angular/router'
import {AuthService} from "./services/auth.service"
import {inject} from "@angular/core"
import {map} from "rxjs/operators"

export const authGuard: CanActivateFn = (route, state) => {
    const auth = inject(AuthService)
    const router = inject(Router)
    return auth.isAuthenticated()
        .pipe(map(value => {
            if (!value) {
                localStorage.setItem('redirectAfterLogin', state.url)
                router.navigate(['login'])
                return false
            }
            return true
        }))
}