import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './views/Dashboard.vue'
import './styles/global.css'

createApp(App).use(createPinia()).mount('#app')
