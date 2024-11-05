import {Injectable} from '@angular/core'
import { HttpClient } from "@angular/common/http"
import {EnvironmentService} from "./enviroment.service"
import {catchError, Observable, of, tap} from "rxjs"
import {map} from "rxjs/operators"

@Injectable({
    providedIn: 'root',
})
export class AuthService {
    public readonly AUTH_TOKEN_KEY = "SYMMIO_AUTH_TOKEN_KEY"
    private serverUrl: string

    constructor(readonly http: HttpClient, readonly environmentService: EnvironmentService) {
        this.serverUrl = environmentService.getValue("serverUrl")
    }

    public getAuthToken(): any | null {
        return localStorage.getItem(this.AUTH_TOKEN_KEY)
    }

    public isAuthenticated(): Observable<boolean> {
        return this.http.get(`${this.serverUrl}/auth/me`)
            .pipe(
                catchError(err => of({})),
                map((value: any) => value.username != null),
            )
    }


    public login(username: string, password: string): Observable<any> {
        let body = new FormData()
        body.append('username', username)
        body.append('password', password)
        return this.http.post(`${this.serverUrl}/auth/login`, body)
            .pipe(tap((value: any) => {
                localStorage.setItem(this.AUTH_TOKEN_KEY, value.access_token)
            }))
    }
}
