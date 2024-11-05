import {computed, effect, Injectable, signal} from "@angular/core"

@Injectable({
    providedIn: "root",
})
export class LoadingService {
    private loadingLevel = signal(0)
    public loading = computed(() => this.loadingLevel() > 0)

    constructor() {
        // effect(() => {
        //     console.log(`The loading level is: ${this.loadingLevel()})`)
        // })
    }

    public setLoading(b: boolean) {
        this.loadingLevel.update(value => b ? value + 1 : Math.max(value - 1, 0))
    }
}
