import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = [ "menu" ]
  static classes = [ "toggle" ]

  toggleMenu() {
    this.menuTarget.classList.toggle(this.toggleClass)
  }
}
