import {Component, ElementRef, Input, AfterViewInit, OnDestroy, ViewChild} from "@angular/core"

@Component({
	selector: "app-glowing-dots",
	template: `<div #container class="glowing-dots-container"></div>`,
	styles: [`
		:host {
			position: absolute;
			inset: 0;
			pointer-events: none;
			z-index: 0;
			overflow: hidden;
		}

		.glowing-dots-container {
			position: absolute;
			inset: 0;
		}
	`],
	standalone: true
})
export class GlowingDotsComponent implements AfterViewInit, OnDestroy {
	@Input() numberOfDots = 10
	@Input() glowSpeed = 12

	@ViewChild("container") containerRef!: ElementRef<HTMLDivElement>

	ngAfterViewInit() {
		const container = this.containerRef.nativeElement
		for (let i = 0; i < this.numberOfDots; i++) {
			this.createDot(container)
		}
	}

	ngOnDestroy() {
		this.containerRef?.nativeElement.replaceChildren()
	}

	private createDot(container: HTMLElement) {
		const dot = document.createElement("div")
		dot.style.cssText = `
			position: absolute;
			width: 3px;
			height: 3px;
			opacity: 0;
			background-color: #FF7A6E;
			box-shadow: 0 0 25px 12px rgba(255, 122, 110, 0.4);
			border-radius: 50%;
			animation: glowingDot ${this.glowSpeed + (Math.random() * 10 - 5)}s ${Math.random() * 5}s infinite ease-in-out;
			top: ${Math.random() * 100}%;
			left: ${Math.random() * 100}%;
		`

		dot.addEventListener("animationiteration", () => {
			dot.style.top = `${Math.random() * 100}%`
			dot.style.left = `${Math.random() * 100}%`
		})

		container.appendChild(dot)
	}
}
