import { browser } from '$app/environment';
import { getBackendConfig, getBanners } from '$lib/apis/configs';
import { getModels } from '$lib/apis/models';
import { getTools } from '$lib/apis/tools';
import { getSessionUser } from '$lib/apis/auths';
import { getLanguages } from '$lib/i18n';
import { getUserSettings } from '$lib/apis/users';
import type { Banner } from '$lib/types';

// if you want to generate a static html file
// for your page.
// Documentation: https://kit.svelte.dev/docs/page-options#prerender
// export const prerender = true;

// if you want to Generate a SPA
// you have to set ssr to false.
// This is not the case (so set as true or comment the line)
// Documentation: https://kit.svelte.dev/docs/page-options#ssr
export const ssr = false;

// How to manage the trailing slashes in the URLs
// the URL for about page will be /about with 'ignore' (default)
// the URL for about page will be /about/ with 'always'
// https://kit.svelte.dev/docs/page-options#trailingslash
export const trailingSlash = 'ignore';

export const load = async ({ fetch }) => {
	const token = browser ? localStorage.getItem('token') : null;

	const promises: [
		Promise<any[]>,
		Promise<any> | undefined,
		Promise<any[]> | undefined,
		Promise<Banner[]> | undefined,
		Promise<any[]> | undefined
	] = [
		getLanguages(fetch).catch((error: any) => {
			console.error('Error loading languages:', error);
			return [];
		}),
		undefined,
		undefined,
		undefined,
		undefined
	];

	if (token) {
		promises[1] = getBackendConfig(token, fetch).catch((error: any) => {
			console.error('Error loading backend config:', error);
			return null;
		});
		promises[2] = getModels(token, fetch).catch((error: any) => {
			console.error('Error loading models:', error);
			return [];
		});
		promises[3] = getBanners(token, fetch).catch((error: any) => {
			console.error('Error loading banners:', error);
			return [];
		});
		promises[4] = getTools(token, fetch).catch((error: any) => {
			console.error('Error loading tools:', error);
			return [];
		});
	}

	const [languages, backendConfig, models, banners, tools] = await Promise.all(promises);

	let sessionUser = null;
	if (token) {
		sessionUser = await getSessionUser(token, fetch).catch((error: any) => {
			console.error('Error loading session user:', error);
			if (browser) {
				localStorage.removeItem('token');
			}
			return null;
		});
	}

	let userSettings = null;
	if (token) {
		userSettings = await getUserSettings(token, fetch).catch((error: any) => {
			console.error('Error loading user settings:', error);
			return null;
		});
	}

	return {
		token,
		sessionUser,
		userSettings,
		backendConfig: backendConfig ?? null,
		models: models ?? [],
		banners: banners ?? [],
		tools: tools ?? [],
		languages
	};
};