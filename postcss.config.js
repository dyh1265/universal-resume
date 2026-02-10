const purgecss = require("@fullhuman/postcss-purgecss")({
  content: ["./docs/*.html"],
  defaultExtractor: content => content.match(/[A-Za-z0-9-_:/.]+/g) || []
});

module.exports = {
  plugins: [
    require("postcss-import"),
    require("@tailwindcss/postcss")({
      config: "./tailwind.config.js"
    }),
    require("autoprefixer"),
    ...process.env.NODE_ENV === "build" ?
      [purgecss, require("cssnano")] : []
  ]
};
