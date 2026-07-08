import { withVueTs, vueTsConfigs } from '@vue/eslint-config-typescript'
import pluginVue from 'eslint-plugin-vue'

export default withVueTs(
  {
    ignores: ['dist/**', 'coverage/**', 'node_modules/**', '.npm-cache/**'],
  },
  ...pluginVue.configs['flat/recommended'],
  vueTsConfigs.recommended,
)
