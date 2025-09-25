import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import sveltePlugin from 'eslint-plugin-svelte'
import globals from 'globals'
import prettier from 'eslint-config-prettier'

export default [
  {
    ignores: ['dist', 'build', '.svelte-kit', 'coverage', 'node_modules']
  },
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node
      }
    }
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...sveltePlugin.configs['flat/recommended'],
  {
    files: ['**/*.svelte'],
    languageOptions: {
      parser: sveltePlugin.parser,
      parserOptions: {
        parser: {
          ts: tseslint.parser
        }
      }
    }
  },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tseslint.parser
    }
  },
  {
    files: ['**/*.spec.ts', '**/*.test.ts'],
    languageOptions: {
      globals: {
        vi: 'readonly',
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly'
      }
    }
  },
  prettier
]
