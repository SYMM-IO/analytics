import { Directive, ElementRef, EventEmitter, OnDestroy, Output } from "@angular/core"

@Directive({
	selector: "[appResizeObserver]",
})
export class ResizeObserverDirective implements OnDestroy {
	@Output() resize = new EventEmitter<DOMRectReadOnly>()

	private observer: ResizeObserver

	constructor(private element: ElementRef) {
		this.observer = new ResizeObserver(entries => {
			for (let entry of entries) {
				this.resize.emit(entry.contentRect)
			}
		})

		this.observer.observe(this.element.nativeElement)
	}

	ngOnDestroy() {
		this.observer.disconnect()
	}
}
