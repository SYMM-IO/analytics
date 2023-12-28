import {Component, Inject} from '@angular/core'
import {AsyncPipe} from "@angular/common"
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms"
import {TuiAlertService, TuiButtonModule, TuiTextfieldControllerModule} from "@taiga-ui/core"
import {TuiInputModule, TuiInputNumberModule, TuiIslandModule} from "@taiga-ui/kit"
import {LoadingService} from "../services/Loading.service"
import {AuthService} from "../auth.service"
import {Router} from "@angular/router"

@Component({
    selector: 'app-login',
    standalone: true,
    imports: [
        AsyncPipe,
        FormsModule,
        TuiButtonModule,
        TuiInputNumberModule,
        TuiIslandModule,
        TuiTextfieldControllerModule,
        ReactiveFormsModule,
        TuiInputModule,
    ],
    templateUrl: './login.component.html',
    styleUrl: './login.component.scss',
})
export class LoginComponent {

    form = new FormGroup({
            username: new FormControl<string>("", [Validators.required]),
            password: new FormControl<string>("", [Validators.required]),
        },
    )

    constructor(readonly loadingService: LoadingService,
                readonly authService: AuthService,
                readonly router: Router,
                @Inject(TuiAlertService) protected readonly alert: TuiAlertService) {
    }

    onLogin() {
        this.authService.login(this.form.value.username!, this.form.value.password!).subscribe({
            next: value => {
                this.alert.open("Logged in successfully").subscribe()
                const redirectPath = localStorage.getItem('redirectAfterLogin') || '/'
                this.router.navigate([redirectPath.slice(1)])
                localStorage.removeItem('redirectAfterLogin')
            },
            error: err => {
                console.error(err);
                this.alert.open(err.error.error_message).subscribe()
            },
        })
    }
}
