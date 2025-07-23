import { WEBUI_BASE_URL } from '$lib/constants';
import { convertOpenApiToToolPayload } from '$lib/utils';
import { getOpenAIModelsDirect } from './openai';

import { parse } from 'yaml';
import { toast } from 'svelte-sonner';

export const getModels = async (
	token: string = '',
	connections: any | null = null,
	base: boolean = false,
	refresh: boolean = false
) => {
	const searchParams = new URLSearchParams();
	if (refresh) {
		searchParams.append('refresh', 'true');
	}

	const res = await fetch(
		`${WEBUI_BASE_URL}/api/models${base ? '/base' : ''}?${searchParams.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const json = await res.json();
	let models = json?.data ?? [];

	if (connections && !base) {
		let localModels: any[] = [];

		if (connections) {
			const OPENAI_API_BASE_URLS = connections.OPENAI_API_BASE_URLS;
			const OPENAI_API_KEYS = connections.OPENAI_API_KEYS;
			const OPENAI_API_CONFIGS = connections.OPENAI_API_CONFIGS;

			const requests = [];
			for (const idx in OPENAI_API_BASE_URLS) {
				const url = OPENAI_API_BASE_URLS[idx];

				if (idx.toString() in OPENAI_API_CONFIGS) {
					const apiConfig = OPENAI_API_CONFIGS[idx.toString()] ?? {};

					const enable = apiConfig?.enable ?? true;
					const modelIds = apiConfig?.model_ids ?? [];

					if (enable) {
						if (modelIds.length > 0) {
							const modelList = {
								object: 'list',
								data: modelIds.map((modelId: string) => ({
									id: modelId,
									name: modelId,
									owned_by: 'openai',
									openai: { id: modelId },
									urlIdx: idx
								}))
							};

							requests.push(
								(async () => {
									return modelList;
								})()
							);
						} else {
							requests.push(
								(async () => {
									try {
										return await getOpenAIModelsDirect(url, OPENAI_API_KEYS[idx]);
									} catch (err) {
										return {
											object: 'list',
											data: [],
											urlIdx: idx
										};
									}
								})()
							);
						}
					} else {
						requests.push(
							(async () => {
								return {
									object: 'list',
									data: [],
									urlIdx: idx
								};
							})()
						);
					}
				}
			}

			const responses = await Promise.all(requests);

			for (const idx in responses) {
				const response = responses[idx];
				const apiConfig = OPENAI_API_CONFIGS[idx.toString()] ?? {};

				let models = Array.isArray(response) ? response : response?.data ?? [];
				models = models.map((model: any) => ({ ...model, openai: { id: model.id }, urlIdx: idx }));

				const prefixId = apiConfig.prefix_id;
				if (prefixId) {
					for (const model of models) {
						model.id = `${prefixId}.${model.id}`;
					}
				}

				const tags = apiConfig.tags;
				if (tags) {
					for (const model of models) {
						model.tags = tags;
					}
				}

				localModels = localModels.concat(models);
			}
		}

		models = models.concat(
			localModels.map((model) => ({
				...model,
				name: model?.name ?? model?.id,
				direct: true
			}))
		);

		// Remove duplicates
		const modelsMap: { [key: string]: any } = {};
		for (const model of models) {
			modelsMap[model.id] = model;
		}

		models = Object.values(modelsMap);
	}

	return models;
};

type ChatCompletedForm = {
	model: string;
	messages: string[];
	chat_id: string;
	session_id: string;
};

export const chatCompleted = async (token: string, body: ChatCompletedForm) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/chat/completed`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

type ChatActionForm = {
	model: string;
	messages: string[];
	chat_id: string;
};

export const chatAction = async (token: string, action_id: string, body: ChatActionForm) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/chat/actions/${action_id}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const stopTask = async (token: string, id: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/tasks/stop/${id}`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getTaskIdsByChatId = async (token: string, chat_id: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/tasks/chat/${chat_id}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getToolServerData = async (token: string, url: string) => {
	const res = await fetch(`${url}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	let spec;
	// Check if URL ends with .yaml or .yml to determine format
	if (url.toLowerCase().endsWith('.yaml') || url.toLowerCase().endsWith('.yml')) {
		const text = await res.text();
		spec = parse(text);
	} else {
		spec = await res.json();
	}

	const data = {
		openapi: spec,
		info: spec.info,
		specs: convertOpenApiToToolPayload(spec)
	};

	console.log(data);
	return data;
};

export const getToolServersData = async (i18n: any, servers: any[]) => {
	return (
		await Promise.all(
			servers
				.filter((server) => server?.config?.enable)
				.map(async (server) => {
					const data = await getToolServerData(
						(server?.auth_type ?? 'bearer') === 'bearer' ? server?.key : localStorage.token,
						(server?.path ?? '').includes('://')
							? server?.path
							: `${server?.url}${(server?.path ?? '').startsWith('/') ? '' : '/'}${server?.path}`
					).catch((err) => {
						toast.error(
							i18n.t(`Failed to connect to {{URL}} OpenAPI tool server`, {
								URL: (server?.path ?? '').includes('://')
									? server?.path
									: `${server?.url}${(server?.path ?? '').startsWith('/') ? '' : '/'}${server?.path}`
							})
						);
						return null;
					});

					if (data) {
						const { openapi, info, specs } = data;
						return {
							url: server?.url,
							openapi: openapi,
							info: info,
							specs: specs
						};
					}
				})
		)
	).filter((server) => server);
};

export const executeToolServer = async (
	token: string,
	url: string,
	name: string,
	params: Record<string, any>,
	serverData: { openapi: any; info: any; specs: any }
) => {
	try {
		// Find the matching operationId in the OpenAPI spec
		const matchingRoute = Object.entries(serverData.openapi.paths).find(([_, methods]) =>
			Object.entries(methods as any).some(([__, operation]: any) => operation.operationId === name)
		);

		if (!matchingRoute) {
			throw new Error(`No matching route found for operationId: ${name}`);
		}

		const [routePath, methods] = matchingRoute;

		const methodEntry = Object.entries(methods as any).find(
			([_, operation]: any) => operation.operationId === name
		);

		if (!methodEntry) {
			throw new Error(`No matching method found for operationId: ${name}`);
		}

		const [httpMethod, operation]: [string, any] = methodEntry;

		// Split parameters by type
		const pathParams: Record<string, any> = {};
		const queryParams: Record<string, any> = {};
		let bodyParams: any = {};

		if (operation.parameters) {
			operation.parameters.forEach((param: any) => {
				const paramName = param.name;
				const paramIn = param.in;
				if (params.hasOwnProperty(paramName)) {
					if (paramIn === 'path') {
						pathParams[paramName] = params[paramName];
					} else if (paramIn === 'query') {
						queryParams[paramName] = params[paramName];
					}
				}
			});
		}

		let finalUrl = `${url}${routePath}`;

		// Replace path parameters (`{param}`)
		Object.entries(pathParams).forEach(([key, value]) => {
			finalUrl = finalUrl.replace(new RegExp(`{${key}}`, 'g'), encodeURIComponent(value));
		});

		// Append query parameters to URL if any
		if (Object.keys(queryParams).length > 0) {
			const queryString = new URLSearchParams(
				Object.entries(queryParams).map(([k, v]) => [k, String(v)])
			).toString();
			finalUrl += `?${queryString}`;
		}

		// Handle requestBody composite
		if (operation.requestBody && operation.requestBody.content) {
			const contentType = Object.keys(operation.requestBody.content)[0];
			if (params !== undefined) {
				bodyParams = params;
			} else {
				// Optional: Fallback or explicit error if body is expected but not provided
				throw new Error(`Request body expected for operation '${name}' but none found.`);
			}
		}

		// Prepare headers and request options
		const headers: Record<string, string> = {
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		};

		let requestOptions: RequestInit = {
			method: httpMethod.toUpperCase(),
			headers
		};

		if (['post', 'put', 'patch'].includes(httpMethod.toLowerCase()) && operation.requestBody) {
			requestOptions.body = JSON.stringify(bodyParams);
		}

		const res = await fetch(finalUrl, requestOptions);
		if (!res.ok) {
			const resText = await res.text();
			throw new Error(`HTTP error! Status: ${res.status}. Message: ${resText}`);
		}

		return await res.json();
	} catch (err: any) {
		const error = err.message;
		console.error('API Request Error:', error);
		return { error };
	}
};

export const getTaskConfig = async (token: string = '') => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/config`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const updateTaskConfig = async (token: string, config: object) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/config/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(config)
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const generateTitle = async (
	token: string = '',
	model: string,
	messages: object[],
	chat_id?: string
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/title/completions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			messages: messages,
			...(chat_id && { chat_id: chat_id })
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();

	try {
		// Step 1: Safely extract the response string
		const response = data?.choices[0]?.message?.content ?? '';

		// Step 2: Attempt to fix common JSON format issues like single quotes
		const sanitizedResponse = response.replace(/['‘’`]/g, '"'); // Convert single quotes to double quotes for valid JSON

		// Step 3: Find the relevant JSON block within the response
		const jsonStartIndex = sanitizedResponse.indexOf('{');
		const jsonEndIndex = sanitizedResponse.lastIndexOf('}');

		// Step 4: Check if we found a valid JSON block (with both `{` and `}`)
		if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
			const jsonResponse = sanitizedResponse.substring(jsonStartIndex, jsonEndIndex + 1);

			// Step 5: Parse the JSON block
			const parsed = JSON.parse(jsonResponse);

			// Step 6: If there's a "tags" key, return the tags array; otherwise, return an empty array
			if (parsed && parsed.title) {
				return parsed.title;
			} else {
				return null;
			}
		}

		// If no valid JSON block found, return an empty array
		return null;
	} catch (e) {
		// Catch and safely return empty array on any parsing errors
		console.error('Failed to parse response: ', e);
		return null;
	}
};

export const generateFollowUps = async (
	token: string = '',
	model: string,
	messages: string,
	chat_id?: string
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/follow_ups/completions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			messages: messages,
			...(chat_id && { chat_id: chat_id })
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();

	try {
		// Step 1: Safely extract the response string
		const response = data?.choices[0]?.message?.content ?? '';

		// Step 2: Attempt to fix common JSON format issues like single quotes
		const sanitizedResponse = response.replace(/['‘’`]/g, '"'); // Convert single quotes to double quotes for valid JSON

		// Step 3: Find the relevant JSON block within the response
		const jsonStartIndex = sanitizedResponse.indexOf('{');
		const jsonEndIndex = sanitizedResponse.lastIndexOf('}');

		// Step 4: Check if we found a valid JSON block (with both `{` and `}`)
		if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
			const jsonResponse = sanitizedResponse.substring(jsonStartIndex, jsonEndIndex + 1);

			// Step 5: Parse the JSON block
			const parsed = JSON.parse(jsonResponse);

			// Step 6: If there's a "follow_ups" key, return the follow_ups array; otherwise, return an empty array
			if (parsed && parsed.follow_ups) {
				return Array.isArray(parsed.follow_ups) ? parsed.follow_ups : [];
			} else {
				return [];
			}
		}

		// If no valid JSON block found, return an empty array
		return [];
	} catch (e) {
		// Catch and safely return empty array on any parsing errors
		console.error('Failed to parse response: ', e);
		return [];
	}
};

export const generateTags = async (
	token: string = '',
	model: string,
	messages: string,
	chat_id?: string
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/tags/completions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			messages: messages,
			...(chat_id && { chat_id: chat_id })
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();

	try {
		// Step 1: Safely extract the response string
		const response = data?.choices[0]?.message?.content ?? '';

		// Step 2: Attempt to fix common JSON format issues like single quotes
		const sanitizedResponse = response.replace(/['‘’`]/g, '"'); // Convert single quotes to double quotes for valid JSON

		// Step 3: Find the relevant JSON block within the response
		const jsonStartIndex = sanitizedResponse.indexOf('{');
		const jsonEndIndex = sanitizedResponse.lastIndexOf('}');

		// Step 4: Check if we found a valid JSON block (with both `{` and `}`)
		if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
			const jsonResponse = sanitizedResponse.substring(jsonStartIndex, jsonEndIndex + 1);

			// Step 5: Parse the JSON block
			const parsed = JSON.parse(jsonResponse);

			// Step 6: If there's a "tags" key, return the tags array; otherwise, return an empty array
			if (parsed && parsed.tags) {
				return Array.isArray(parsed.tags) ? parsed.tags : [];
			} else {
				return [];
			}
		}

		// If no valid JSON block found, return an empty array
		return [];
	} catch (e) {
		// Catch and safely return empty array on any parsing errors
		console.error('Failed to parse response: ', e);
		return [];
	}
};

export const generateEmoji = async (
	token: string = '',
	model: string,
	prompt: string,
	chat_id?: string
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/emoji/completions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			prompt: prompt,
			...(chat_id && { chat_id: chat_id })
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();
	const response = data?.choices[0]?.message?.content.replace(/["']/g, '') ?? null;

	if (response) {
		if (/\p{Extended_Pictographic}/u.test(response)) {
			return response.match(/\p{Extended_Pictographic}/gu)[0];
		}
	}

	return null;
};

export const generateQueries = async (
	token: string = '',
	model: string,
	messages: object[],
	prompt: string,
	type: string = 'web_search'
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/queries/completions`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			messages: messages,
			prompt: prompt,
			type: type
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();
	// Step 1: Safely extract the response string
	const response = data?.choices[0]?.message?.content ?? '';

	try {
		const jsonStartIndex = response.indexOf('{');
		const jsonEndIndex = response.lastIndexOf('}');

		if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
			const jsonResponse = response.substring(jsonStartIndex, jsonEndIndex + 1);

			// Step 5: Parse the JSON block
			const parsed = JSON.parse(jsonResponse);

			// Step 6: If there's a "queries" key, return the queries array; otherwise, return an empty array
			if (parsed && parsed.queries) {
				return Array.isArray(parsed.queries) ? parsed.queries : [];
			} else {
				return [];
			}
		}

		// If no valid JSON block found, return response as is
		return [response];
	} catch (e) {
		// Catch and safely return empty array on any parsing errors
		console.error('Failed to parse response: ', e);
		return [response];
	}
};

export const generateAutoCompletion = async (
	token: string = '',
	model: string,
	prompt: string,
	messages?: object[],
	type: string = 'search query'
) => {
	const controller = new AbortController();

	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/auto/completions`, {
		signal: controller.signal,
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			prompt: prompt,
			...(messages && { messages: messages }),
			type: type,
			stream: false
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const data = await res.json();
	const response = data?.choices[0]?.message?.content ?? '';

	try {
		const jsonStartIndex = response.indexOf('{');
		const jsonEndIndex = response.lastIndexOf('}');

		if (jsonStartIndex !== -1 && jsonEndIndex !== -1) {
			const jsonResponse = response.substring(jsonStartIndex, jsonEndIndex + 1);

			// Step 5: Parse the JSON block
			const parsed = JSON.parse(jsonResponse);

			// Step 6: If there's a "queries" key, return the queries array; otherwise, return an empty array
			if (parsed && parsed.text) {
				return parsed.text;
			} else {
				return '';
			}
		}

		// If no valid JSON block found, return response as is
		return response;
	} catch (e) {
		// Catch and safely return empty array on any parsing errors
		console.error('Failed to parse response: ', e);
		return response;
	}
};

export const generateMoACompletion = async (
	token: string = '',
	model: string,
	prompt: string,
	responses: string[]
) => {
	const controller = new AbortController();

	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/tasks/moa/completions`, {
		signal: controller.signal,
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			model: model,
			prompt: prompt,
			responses: responses,
			stream: true
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return [res, controller];
};

export const getPipelinesList = async (token: string = '') => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/pipelines/list`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const json = await res.json();
	return json?.data ?? [];
};

export const uploadPipeline = async (token: string, file: File, urlIdx: string) => {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('urlIdx', urlIdx);

	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/pipelines/upload`, {
		method: 'POST',
		headers: {
			...(token && { authorization: `Bearer ${token}` })
			// 'Content-Type': 'multipart/form-data' is not needed as Fetch API will set it automatically
		},
		body: formData
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const downloadPipeline = async (token: string, url: string, urlIdx: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/pipelines/add`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			url: url,
			urlIdx: urlIdx
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const deletePipeline = async (token: string, id: string, urlIdx: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/pipelines/delete`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({
			id: id,
			urlIdx: urlIdx
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getPipelines = async (token: string, urlIdx?: string) => {
	const searchParams = new URLSearchParams();
	if (urlIdx !== undefined) {
		searchParams.append('urlIdx', urlIdx);
	}

	const res = await fetch(`${WEBUI_BASE_URL}/api/v1/pipelines/?${searchParams.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	const json = await res.json();
	return json?.data ?? [];
};

export const getPipelineValves = async (
	token: string,
	pipeline_id: string,
	urlIdx: string
) => {
	const searchParams = new URLSearchParams();
	if (urlIdx !== undefined) {
		searchParams.append('urlIdx', urlIdx);
	}

	const res = await fetch(
		`${WEBUI_BASE_URL}/api/v1/pipelines/${pipeline_id}/valves?${searchParams.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getPipelineValvesSpec = async (token: string, pipeline_id: string, urlIdx: string) => {
	const searchParams = new URLSearchParams();
	if (urlIdx !== undefined) {
		searchParams.append('urlIdx', urlIdx);
	}

	const res = await fetch(
		`${WEBUI_BASE_URL}/api/v1/pipelines/${pipeline_id}/valves/spec?${searchParams.toString()}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			}
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const updatePipelineValves = async (
	token: string = '',
	pipeline_id: string,
	valves: object,
	urlIdx: string
) => {
	const searchParams = new URLSearchParams();
	if (urlIdx !== undefined) {
		searchParams.append('urlIdx', urlIdx);
	}

	const res = await fetch(
		`${WEBUI_BASE_URL}/api/v1/pipelines/${pipeline_id}/valves/update?${searchParams.toString()}`,
		{
			method: 'POST',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { authorization: `Bearer ${token}` })
			},
			body: JSON.stringify(valves)
		}
	);

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getUsage = async (token: string = '') => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/usage`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` })
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getBackendConfig = async () => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/config`, {
		method: 'GET',
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json'
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getChangelog = async () => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/changelog`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json'
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getVersionUpdates = async (token: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/version/updates`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getModelFilterConfig = async (token: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/config/model/filter`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const updateModelFilterConfig = async (
	token: string,
	enabled: boolean,
	models: string[]
) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/config/model/filter`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			enabled: enabled,
			models: models
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getWebhookUrl = async (token: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/webhook`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}
	const json = await res.json();
	return json.url;
};

export const updateWebhookUrl = async (token: string, url: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/webhook`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			url: url
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}
	const json = await res.json();
	return json.url;
};

export const getCommunitySharingEnabledStatus = async (token: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/community_sharing`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const toggleCommunitySharingEnabledStatus = async (token: string) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/community_sharing/toggle`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};

export const getModelConfig = async (token: string): Promise<GlobalModelConfig> => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/config/models`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}
	const json = await res.json();
	return json.models;
};

export interface ModelConfig {
	id: string;
	name: string;
	meta: ModelMeta;
	base_model_id?: string;
	params: ModelParams;
}

export interface ModelMeta {
	toolIds: never[];
	description?: string;
	capabilities?: object;
	profile_image_url?: string;
}

export interface ModelParams {}

export type GlobalModelConfig = ModelConfig[];

export const updateModelConfig = async (token: string, config: GlobalModelConfig) => {
	const res = await fetch(`${WEBUI_BASE_URL}/api/config/models`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			models: config
		})
	});

	if (!res.ok) {
		const error = await res.json().catch(() => null);
		throw new Error(error?.detail ?? res.statusText);
	}

	return await res.json();
};
