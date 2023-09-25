import {Injectable, NgZone} from '@angular/core';
import {InMemoryCache} from '@apollo/client/core';
import {HttpLink} from 'apollo-angular/http';
import {Apollo} from "apollo-angular";

@Injectable({
	providedIn: 'root',
})
export class ApolloManagerService {

	private clients: Map<string, Apollo> = new Map();

	constructor(private httpLink: HttpLink, readonly ngZone: NgZone) {
	}

	createClient(uri: string): Apollo {
		const client = new Apollo(this.ngZone, {
			cache: new InMemoryCache(),
			link: this.httpLink.create({uri}),
		});
		this.clients.set(uri, client);
		return client;
	}

	getClient(uri: string): Apollo | undefined {
		if (!this.clients.has(uri))
			this.createClient(uri);
		return this.clients.get(uri);
	}
}
