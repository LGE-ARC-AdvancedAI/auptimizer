module.exports = {
  module: {
    rules: [
      {
        test: /\.scss$/,
        loader: 'postcss-loader',
        options: {
          ident: 'postcss',
          plugins: () => [require('tailwindcss'), require('autoprefixer')]
        }
      }
    ]
  }
};
