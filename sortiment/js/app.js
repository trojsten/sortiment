import { Application } from "@hotwired/stimulus"
import * as Turbo from "@hotwired/turbo"

window.Stimulus = Application.start()

import BarcodeController from "./controllers/barcode"
Stimulus.register("barcode", BarcodeController)
import ImportController from "./controllers/import"
Stimulus.register("import", ImportController)
import MenuToggleController from "./controllers/menu-toggle"
Stimulus.register("menu-toggle", MenuToggleController)

Turbo.start()

document.addEventListener("turbo:before-fetch-request", (event) => {
	const tokenMeta = document.querySelector('meta[name="csrf-token"]')
	const token = tokenMeta.getAttribute("value")
	event.detail.fetchOptions.headers["X-CSRFToken"] = token
})

document.addEventListener("turbo:load", (event) => {
    if (typeof window.djdt !== "undefined") {
        djdt.init()
    }
})
