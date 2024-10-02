import { TuiButtonLoading } from "@taiga-ui/kit";
import { TuiIslandDirective, TuiTextfieldControllerModule, TuiInputModule, TuiInputNumberModule } from "@taiga-ui/legacy";
import {Component, Inject} from '@angular/core'
import {AsyncPipe} from "@angular/common"
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule, Validators} from "@angular/forms"
import { TuiAlertService, TuiButton } from "@taiga-ui/core"
import {LoadingService} from "../services/Loading.service"
import {AuthService} from "../services/auth.service"
import {Router} from "@angular/router"
import {TuiCardLarge} from "@taiga-ui/layout";

@Component({
    selector: 'app-login',
    standalone: true,
	imports: [
		AsyncPipe,
		FormsModule,
		TuiButton,
		TuiInputNumberModule,
		TuiIslandDirective,
		TuiTextfieldControllerModule,
		ReactiveFormsModule,
		TuiInputModule,
		TuiButtonLoading,
		TuiCardLarge
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
