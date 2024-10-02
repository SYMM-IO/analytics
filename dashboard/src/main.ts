import {platformBrowserDynamic} from '@angular/platform-browser-dynamic';

import {AppModule} from './app/app.module';

import 'echarts/theme/dark.js';

platformBrowserDynamic()
    .bootstrapModule(AppModule)
    .catch((err) => console.error(err));
