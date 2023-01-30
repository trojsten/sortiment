/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        './sortiment/**/*.{html,js}',
    ],
    theme: {
        extend: {},
    },
    variants: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
