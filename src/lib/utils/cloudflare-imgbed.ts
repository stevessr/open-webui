/**
 * CloudFlare-ImgBed 图片上传工具
 * 支持通过 CloudFlare-ImgBed 项目上传图片
 */

export interface CloudFlareImgBedConfig {
	baseUrl: string; // 例如：https://your.domain
	authCode?: string; // 上传认证码
	apiToken?: string; // API Token (需要 upload 权限)
	uploadChannel?: 'telegram' | 'cfr2' | 's3'; // 上传渠道
	serverCompress?: boolean; // 服务端压缩
	autoRetry?: boolean; // 失败时自动切换渠道重试
	uploadNameType?: 'default' | 'index' | 'origin' | 'short'; // 文件命名方式
	returnFormat?: 'default' | 'full'; // 返回链接格式
	uploadFolder?: string; // 上传目录
	headers?: Record<string, string>; // 额外的请求头
}

export interface ImgBedUploadResponse {
	status: boolean;
	url?: string;
	message?: string;
	data?: {
		url: string;
		filename: string;
		size: number;
	};
}

export interface ImgBedUploadError {
	error: string;
	message: string;
}

/**
 * 上传图片到 CloudFlare-ImgBed
 * @param config CloudFlare-ImgBed 配置
 * @param file 要上传的图片文件
 * @returns 上传结果
 */
export async function uploadImageToImgBed(
	config: CloudFlareImgBedConfig,
	file: File
): Promise<ImgBedUploadResponse> {
	const {
		baseUrl,
		authCode,
		apiToken,
		uploadChannel = 'telegram',
		serverCompress = true,
		autoRetry = true,
		uploadNameType = 'default',
		returnFormat = 'default',
		uploadFolder,
		headers = {}
	} = config;

	// 构建上传 URL 和查询参数
	const uploadUrl = new URL(`${baseUrl}/upload`);

	// 添加查询参数
	if (authCode) {
		uploadUrl.searchParams.append('authCode', authCode);
	}
	uploadUrl.searchParams.append('serverCompress', serverCompress.toString());
	uploadUrl.searchParams.append('uploadChannel', uploadChannel);
	uploadUrl.searchParams.append('autoRetry', autoRetry.toString());
	uploadUrl.searchParams.append('uploadNameType', uploadNameType);
	uploadUrl.searchParams.append('returnFormat', returnFormat);
	if (uploadFolder) {
		uploadUrl.searchParams.append('uploadFolder', uploadFolder);
	}

	try {
		const formData = new FormData();
		formData.append('file', file);

		// 构建请求头
		const requestHeaders: Record<string, string> = {
			'Accept': 'application/json',
			'User-Agent': 'Open-WebUI-ImgBed-Client/1.0',
			...headers
		};

		// 添加 API Token 认证
		if (apiToken) {
			requestHeaders['Authorization'] = `Bearer ${apiToken}`;
		}

		console.log('Uploading to ImgBed:', {
			url: uploadUrl.toString(),
			fileName: file.name,
			fileSize: file.size
		});

		const response = await fetch(uploadUrl.toString(), {
			method: 'POST',
			body: formData,
			headers: requestHeaders
		});

		if (!response.ok) {
			const errorText = await response.text();
			throw new Error(`HTTP ${response.status}: ${errorText}`);
		}

		const result = await response.json();
		console.log('ImgBed response:', result);

		// 处理响应格式：[{ "src": "/file/abc123_image.jpg" }]
		if (Array.isArray(result) && result.length > 0 && result[0].src) {
			const imagePath = result[0].src;

			// 确保 baseUrl 没有尾部斜杠，imagePath 以 / 开头
			const cleanBaseUrl = baseUrl.replace(/\/$/, '');
			const fullUrl = returnFormat === 'full' && imagePath.startsWith('http')
				? imagePath
				: `${cleanBaseUrl}${imagePath}`;

			console.log('Image URL constructed:', {
				imagePath,
				cleanBaseUrl,
				fullUrl,
				returnFormat
			});

			return {
				status: true,
				url: fullUrl,
				data: {
					url: fullUrl,
					filename: file.name,
					size: file.size
				}
			};
		} else {
			throw new Error('Invalid response format from ImgBed');
		}
	} catch (error) {
		console.error('ImgBed upload error:', error);
		throw error;
	}
}

/**
 * 检查 CloudFlare-ImgBed 服务是否可用
 * @param config CloudFlare-ImgBed 配置
 * @returns 服务状态
 */
export async function checkImgBedStatus(config: CloudFlareImgBedConfig): Promise<boolean> {
	try {
		const response = await fetch(config.baseUrl, {
			method: 'GET',
			headers: {
				'Accept': 'text/html,application/json'
			}
		});
		return response.ok;
	} catch {
		return false;
	}
}

/**
 * 获取 CloudFlare-ImgBed 上传配置
 * @returns 默认配置
 */
export function getImgBedConfig(): CloudFlareImgBedConfig {
	// 从环境变量或配置中读取
	const baseUrl = import.meta.env.VITE_CLOUDFLARE_IMGBED_URL || 'https://your.domain';
	const authCode = import.meta.env.VITE_CLOUDFLARE_IMGBED_AUTH_CODE;
	const apiToken = import.meta.env.VITE_CLOUDFLARE_IMGBED_API_TOKEN;

	return {
		baseUrl,
		authCode,
		apiToken,
		uploadChannel: 'telegram',
		serverCompress: true,
		autoRetry: true,
		uploadNameType: 'default',
		returnFormat: 'default',
		headers: {
			'User-Agent': 'Open-WebUI-ImgBed-Client/1.0'
		}
	};
}