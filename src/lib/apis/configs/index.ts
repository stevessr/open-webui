import { WEBUI_API_BASE_URL, WEBUI_COOMMON_API_BASE_URL } from '$lib/constants';
import type { Banner } from '$lib/types';

export const importConfig = async (token: string, config: any, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/import`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			config: config
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const exportConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/export`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getConnectionsConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/connections`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setConnectionsConfig = async (
	token: string,
	config: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/connections`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...config
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getToolServerConnections = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/tool_servers`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setToolServerConnections = async (
	token: string,
	connections: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/tool_servers`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...connections
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const verifyToolServerConnection = async (
	token: string,
	connection: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/tool_servers/verify`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...connection
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getCodeExecutionConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/code_execution`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setCodeExecutionConfig = async (
	token: string,
	config: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/code_execution`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...config
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getModelsConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/models`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setModelsConfig = async (
	token: string,
	config: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/models`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...config
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setDefaultPromptSuggestions = async (
	token: string,
	promptSuggestions: string,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/suggestions`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			suggestions: promptSuggestions
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getBanners = async (
	token: string,
	fetchFn: typeof fetch = fetch
): Promise<Banner[]> => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/banners`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const setBanners = async (
	token: string,
	banners: Banner[],
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/banners`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			banners: banners
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getCustomStylesConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/custom_styles`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};

export const getBackendConfig = async (token: string, fetchFn: typeof fetch = fetch) => {
	const res = await fetchFn(`${WEBUI_COOMMON_API_BASE_URL}/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		throw await res.json();
	}

	return await res.json();
};

export const setCustomStylesConfig = async (
	token: string,
	config: object,
	fetchFn: typeof fetch = fetch
) => {
	const res = await fetchFn(`${WEBUI_API_BASE_URL}/configs/custom_styles`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...config
		})
	});

	if (!res.ok) {
		throw await res.json();
	}

	return res.json();
};
