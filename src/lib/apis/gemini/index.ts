import { Gemini_API_BASE_URL , WEBUI_BASE_URL } from '$lib/constants';

export const getGeminiConfig = async (token: string) => {
	let error = null;

	const res = await fetch(`${Gemini_API_BASE_URL}/config`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updateGeminiConfig = async (token: string, data: any) => {
	let error = null;

	const res = await fetch(`${Gemini_API_BASE_URL}/config/update`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getGeminiModels = async (token: string) => {
	let error = null;

	const res = await fetch(`${Gemini_API_BASE_URL}/models`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const verifyGeminiConnection = async (token: string, data: any) => {
	let error = null;

	const res = await fetch(`${Gemini_API_BASE_URL}/verify`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(data)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const generateGeminiChat = async (
	token: string = '',
	body: object
) => {
	let error = null;

	const res = await fetch(`${Gemini_API_BASE_URL}/chat/completions`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		credentials: 'include',
		body: JSON.stringify(body)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export const generateGeminiContent = async (
	token: string = '',
	model: string,
	contents: any[],
	generationConfig: any = {}
) => {
	let error = null;

	const geminiPayload = {
		contents,
		generationConfig
	};

	const res = await fetch(`${Gemini_API_BASE_URL}/models/${model}:generateContent`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		credentials: 'include',
		body: JSON.stringify(geminiPayload)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}

export const streamGeminiContent = async (
	token: string = '',
	model: string,
	contents: any[],
	generationConfig: any = {}
) => {
	let error = null;

	const geminiPayload = {
		contents,
		generationConfig
	};

	const res = await fetch(`${Gemini_API_BASE_URL}/models/${model}:streamGenerateContent`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		credentials: 'include',
		body: JSON.stringify(geminiPayload)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res;
		})
		.catch((err) => {
			console.log(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
}