module.exports = {
  important: true,
  theme: {
    screens: {
      xs: '599px',
      sm: '600px',
      md: '960px',
      lg: '1280px',
      xl: '1920px',
    },
    cursor: {
      crosshair: 'crosshair',
      'zoom-in': 'zoom-in',
    },
    container: {
      center: true,
    },
  },
  variants: {
    borderColor: ['responsive', 'hover', 'focus', 'group-hover'],
  },
  corePlugins: {
    outline: false,
    borderColor: false,
  },
  plugins: [
    function ({ addUtilities }) {
      const newUtilities = {
        '.truncate-none': {
          overflow: 'unset',
          'text-overflow': 'unset',
          'white-space': 'unset',
        },
      };

      addUtilities(newUtilities, {
        variants: ['responsive'],
      });
    },
  ],
};
