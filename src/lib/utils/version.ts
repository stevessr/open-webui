import { get } from 'svelte/store';
import { config } from '$lib/stores';
import { WEBUI_VERSION } from '$lib/constants';
import { writable } from 'svelte/store';
import { toast } from 'svelte-sonner';
import UpdateInfoToast from '$lib/components/layout/UpdateInfoToast.svelte';

export const version = writable({
	current: WEBUI_VERSION,
	latest: ''
});

export const updateAvailable = writable<{ current: string; latest: string } | null>(null);

export const checkForVersionUpdates = async () => {
	updateAvailable.set(null);

	const res = await fetch('https://api.github.com/repos/open-webui/open-webui/releases/latest');

	if (res.ok) {
		const data = await res.json();
		const latestVersion = data.tag_name.slice(1); // Remove 'v' from tag

		version.set({
			current: WEBUI_VERSION,
			latest: latestVersion
		});
	} else {
		version.set({
			current: WEBUI_VERSION,
			latest: ''
		});
	}

	const configValue = get(config);

	if (configValue?.features?.enable_version_update_check === false) {
		return;
	}

	// Check if the user has dismissed the update toast in the last 24 hours
	if (localStorage.dismissedUpdateToast) {
		const dismissedUpdateToast = new Date(Number(localStorage.dismissedUpdateToast));
		const now = new Date();

		if (now.getTime() - dismissedUpdateToast.getTime() > 24 * 60 * 60 * 1000) {
			// 24 hours have passed, so we can show the toast again
			localStorage.removeItem('dismissedUpdateToast');
		} else {
			// Less than 24 hours have passed, so we should not show the toast
			return;
		}
	}

	const versionValue = get(version);

	if (versionValue.latest && versionValue.current !== versionValue.latest) {
		toast.info('New version available!', {
			component: UpdateInfoToast,
			componentProps: {
				version: versionValue
			}
		});
	}
};
