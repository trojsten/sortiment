import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "form", "field", "firstProduct", "productFrame" ]

  connect() {
    this.shouldSelect = false
    this.productFrameTarget.addEventListener("turbo:frame-load", this.executeSelection)
    this.focusInterval = setInterval(() => {
      this.fieldTarget.focus()
    }, 2000)
  }

  disconnect() {
    this.productFrameTarget.removeEventListener("turbo:frame-load", this.executeSelection)
    clearTimeout(this.timeout)
    clearInterval(this.focusInterval)
  }

  search() {
    clearTimeout(this.timeout)
    this.timeout = setTimeout(() => {
      this.formTarget.requestSubmit()
    }, 200)
  }

  select() {
    if (this.timeout) {
      this.shouldSelect = true
    } else {
      this.executeSelection()
    }
  }

  executeSelection = (event) => {
    if (!this.shouldSelect || !this.hasFirstProductTarget) {
      return
    }

    this.shouldSelect = false
    this.firstProductTarget.click()
  }
}
