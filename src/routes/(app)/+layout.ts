import { getModels, getToolServersData, getVersionUpdates } from '$lib/apis';
import { getBanners } from '$lib/apis/configs';
import { getTools } from '$lib/apis/tools';
import { getUserSettings } from '$lib/apis/users';
import { WEBUI_VERSION } from '$lib/constants';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch, depends }) => {
	const token = localStorage.getItem('token');

	if (!token) {
		return {};
	}

	depends('layout:data');

	const userSettings = await getUserSettings(token, fetch).catch(() => null);

	const [models, banners, tools, version] = await Promise.all([
		getModels(token, undefined, undefined, undefined, fetch).catch(() => []),
		getBanners(token, fetch).catch(() => []),
		getTools(token, fetch).catch(() => []),
		getVersionUpdates(token, fetch).catch(() => ({
			current: WEBUI_VERSION,
			latest: WEBUI_VERSION
		}))
	]);

	return {
		userSettings,
		models,
		banners,
		tools,
		version
	};
};
