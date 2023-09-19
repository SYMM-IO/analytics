import {Inject, Injectable, InjectionToken, Optional} from "@angular/core";

export const ENVIRONMENT = new InjectionToken<{ [key: string]: any }>('environment');

@Injectable({
    providedIn: 'root',
})
export class EnvironmentService {
    private readonly environment: any;

    // We need @Optional to be able to start app without providing environment file
    constructor(@Optional() @Inject(ENVIRONMENT) environment: any) {
        this.environment = environment !== null ? environment : {};
    }

    getValue(key: string, defaultValue?: any): any {
        return this.environment[key] || defaultValue;
    }
}