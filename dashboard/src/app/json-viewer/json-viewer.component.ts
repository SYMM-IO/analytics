import {Component, Inject} from '@angular/core'
import {TuiDialogContext, TuiDialogService} from "@taiga-ui/core"
import {POLYMORPHEUS_CONTEXT} from "@tinkoff/ng-polymorpheus"
import {NgxJsonViewerModule} from "ngx-json-viewer"

@Component({
    selector: 'app-json-viewer',
    standalone: true,
    imports: [
        NgxJsonViewerModule,
    ],
    templateUrl: './json-viewer.component.html',
    styleUrl: './json-viewer.component.scss',
})
export class JsonViewerComponent {
    constructor(@Inject(TuiDialogService) private readonly dialogs: TuiDialogService,
                @Inject(POLYMORPHEUS_CONTEXT)
                readonly context: TuiDialogContext<number, number>) {
    }
}
