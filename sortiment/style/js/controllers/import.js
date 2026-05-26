import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
	static targets = [ "zero", "unitPrice", "totalPrice", "quantity", "suggestion" ]
	static values = { currentPrice: Number, currentQuantity: Number }

	connect() {
		// this.zeroTarget.style.display = "none"
		this.reset()
	}

	reset() {
		this.unitPriceTarget.value = 0
		this.totalPriceTarget.value = 0
	}

	showZeroIfNeeded() {
		if (this.unitPriceTarget.value <= 0) {
			this.zeroTarget.classList.remove("hidden")
		} else {
			this.zeroTarget.classList.add("hidden")
		}
	}

	updateTotalPrice() {
		const unitPrice = parseFloat(this.unitPriceTarget.value)
		const quantity = parseFloat(this.quantityTarget.value)
		this.totalPriceTarget.value = (unitPrice * quantity).toFixed(2)
		this.showZeroIfNeeded()
		this.updateSuggestedSellPrice()
	}

	updateUnitPrice() {
		const totalPrice = parseFloat(this.totalPriceTarget.value)
		const quantity = parseFloat(this.quantityTarget.value)
		this.unitPriceTarget.value = (totalPrice / quantity).toFixed(2)
		this.showZeroIfNeeded()
		this.updateSuggestedSellPrice()
	}

	updateSuggestedSellPrice() {
		const totalPrice = parseFloat(this.totalPriceTarget.value)
		const quantity = parseFloat(this.quantityTarget.value)

		let suggestion = (this.currentPriceValue + totalPrice) / (this.currentQuantityValue + quantity)
		if (Number.isNaN(suggestion)) {
			suggestion = 0.0
		}
		this.suggestionTarget.innerText = suggestion.toFixed(3)
	}
}
