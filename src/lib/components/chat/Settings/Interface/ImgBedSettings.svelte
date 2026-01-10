<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { settings } from '$lib/stores';
	import { checkImgBedStatus, type CloudFlareImgBedConfig } from '$lib/utils/cloudflare-imgbed';
	import Switch from '$lib/components/common/Switch.svelte';
	import Select from '$lib/components/common/Select.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	export let saveSettings: Function;
	export let show = false;

	// CloudFlare-ImgBed 配置
	let useImgBed = false;
	let imgBedConfig: CloudFlareImgBedConfig = {
		baseUrl: '',
		authCode: '',
		apiToken: '',
		uploadChannel: 'telegram',
		serverCompress: true,
		autoRetry: true,
		uploadNameType: 'default',
		returnFormat: 'default',
		uploadFolder: ''
	};

	const uploadChannelItems = [
		{ value: 'telegram', label: 'Telegram' },
		{ value: 'cfr2', label: 'CF R2' },
		{ value: 's3', label: 'S3' },
		{ value: 'discord', label: 'Discord' },
		{ value: 'huggingface', label: 'HuggingFace' },
		{ value: 'external', label: 'External' }
	];

	$: nameTypeItems = [
		{ value: 'default', label: $i18n.t('Default (prefix_name)') },
		{ value: 'index', label: $i18n.t('Index Only') },
		{ value: 'origin', label: $i18n.t('Original Name') },
		{ value: 'short', label: $i18n.t('Short Link') }
	];

	$: returnFormatItems = [
		{ value: 'default', label: $i18n.t('Default (/file/id)') },
		{ value: 'full', label: $i18n.t('Full URL') }
	];

	let checkingStatus = false;
	let serviceStatus = false;
	let showAuthCode = false;
	let showApiToken = false;

	const toggleUseImgBed = async () => {
		if (!useImgBed && imgBedConfig.baseUrl) {
			// 如果启用图床，先检查连接状态
			const status = await checkImgBedService();
			if (!status) {
				toast.error($i18n.t('ImgBed service is not accessible, please check the URL'));
				useImgBed = false;
				return;
			}
		}
		saveSettings({
			useImgBed,
			imgBedConfig
		});
	};

	const checkImgBedService = async () => {
		if (!imgBedConfig.baseUrl) return false;

		checkingStatus = true;
		try {
			serviceStatus = await checkImgBedStatus(imgBedConfig);
			return serviceStatus;
		} catch (error) {
			console.error('Error checking ImgBed status:', error);
			serviceStatus = false;
			return false;
		} finally {
			checkingStatus = false;
		}
	};

	const saveImgBedConfig = async () => {
		if (!imgBedConfig.baseUrl) {
			toast.error($i18n.t('Please enter ImgBed base URL'));
			return;
		}

		// 验证 URL 格式
		try {
			new URL(imgBedConfig.baseUrl);
		} catch {
			toast.error($i18n.t('Invalid URL format'));
			return;
		}

		// 检查服务状态
		const status = await checkImgBedService();
		if (!status) {
			toast.error($i18n.t('ImgBed service is not accessible, please check the URL'));
			return;
		}

		saveSettings({
			useImgBed,
			imgBedConfig
		});
		toast.success($i18n.t('ImgBed configuration saved successfully'));
	};

	const resetImgBedConfig = () => {
		imgBedConfig = {
			baseUrl: '',
			authCode: '',
			apiToken: '',
			uploadChannel: 'telegram',
			serverCompress: true,
			autoRetry: true,
			uploadNameType: 'default',
			returnFormat: 'default',
			uploadFolder: ''
		};
		useImgBed = false;
		saveSettings({
			useImgBed,
			imgBedConfig
		});
		toast.success($i18n.t('ImgBed configuration reset'));
	};

	const testImgBedConnection = async () => {
		if (!imgBedConfig.baseUrl) {
			toast.error($i18n.t('Please enter ImgBed base URL'));
			return;
		}

		const status = await checkImgBedService();
		if (status) {
			toast.success($i18n.t('ImgBed service is accessible'));
		} else {
			toast.error($i18n.t('ImgBed service is not accessible'));
		}
	};

	const submitHandler = async () => {
		await saveImgBedConfig();
		show = false;
	};

	onMount(async () => {
		// 从设置中加载配置
		useImgBed = $settings?.useImgBed ?? false;
		imgBedConfig = $settings?.imgBedConfig ?? {
			baseUrl: 'https://your.domain',
			authCode: '',
			apiToken: '',
			uploadChannel: 'telegram',
			serverCompress: true,
			autoRetry: true,
			uploadNameType: 'default',
			returnFormat: 'default',
			uploadFolder: ''
		};

		// 如果有配置，检查服务状态
		if (imgBedConfig.baseUrl) {
			await checkImgBedService();
		}
	});

	$: serviceStatusText = serviceStatus
		? $i18n.t('Connected')
		: $i18n.t('Disconnected');
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 pb-1.5">
			<h1 class="text-lg font-medium self-center font-primary">
				{$i18n.t('Image Hosting Settings')}
			</h1>
			<button
				class="self-center"
				aria-label={$i18n.t('Close modal')}
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="p-4 space-y-4 dark:text-gray-200">
			<!-- 启用图床 -->
			<div class="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-700">
				<div class="flex-1">
					<label for="use-img-bed" class="text-sm font-medium text-gray-900 dark:text-white">
						{$i18n.t('Use CloudFlare ImgBed')}
					</label>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('Upload images to external ImgBed service instead of local storage')}
					</p>
				</div>
				<Switch id="use-img-bed" bind:state={useImgBed} on:change={toggleUseImgBed} />
			</div>

			<form
				class="grid grid-cols-1 md:grid-cols-4 gap-4"
				on:submit|preventDefault={submitHandler}
			>
				<!-- 基础配置 -->
				<div class="md:col-span-2">
					<label for="img-bed-url" class="block text-sm font-medium text-gray-900 dark:text-white mb-2">
						{$i18n.t('ImgBed Base URL')}
					</label>
					<input
						id="img-bed-url"
						type="url"
						placeholder="https://your.domain"
						bind:value={imgBedConfig.baseUrl}
						class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('The base URL of your CloudFlare ImgBed instance')}
					</p>
				</div>

				<div class="md:col-span-1 lg:col-span-2">
					<label
						for="img-bed-auth-code"
						class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
					>
						{$i18n.t('Auth Code (Optional)')}
					</label>
					<div class="relative">
						<input
							id="img-bed-auth-code"
							type={showAuthCode ? 'text' : 'password'}
							placeholder="your-auth-code"
							bind:value={imgBedConfig.authCode}
							class="w-full px-3 py-2 pr-10 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
						<button
							type="button"
							class="absolute inset-y-0 right-0 px-3 flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
							on:click={() => (showAuthCode = !showAuthCode)}
						>
							{showAuthCode ? 'Hide' : 'Show'}
						</button>
					</div>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('Authentication code for your ImgBed service')}
					</p>
				</div>

				<div class="md:col-span-1 lg:col-span-2">
					<label
						for="img-bed-api-token"
						class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
					>
						{$i18n.t('API Token (Optional)')}
					</label>
					<div class="relative">
						<input
							id="img-bed-api-token"
							type={showApiToken ? 'text' : 'password'}
							placeholder="your-api-token"
							bind:value={imgBedConfig.apiToken}
							class="w-full px-3 py-2 pr-10 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
						<button
							type="button"
							class="absolute inset-y-0 right-0 px-3 flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
							on:click={() => (showApiToken = !showApiToken)}
						>
							{showApiToken ? 'Hide' : 'Show'}
						</button>
					</div>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('API token if your ImgBed service requires token authentication')}
					</p>
				</div>

				<div class="md:col-span-2 lg:col-span-1">
					<label
						for="upload-channel"
						class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
					>
						{$i18n.t('Upload Channel')}
					</label>
					<Select
						id="upload-channel"
						bind:value={imgBedConfig.uploadChannel}
						items={uploadChannelItems}
						className="w-full rounded-lg text-sm"
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('Storage channel for uploaded images')}
					</p>
				</div>

				<div class="md:col-span-2 lg:col-span-3">
					<label
						for="upload-folder"
						class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
					>
						{$i18n.t('Upload Folder (Optional)')}
					</label>
					<input
						id="upload-folder"
						type="text"
						placeholder="img/test"
						bind:value={imgBedConfig.uploadFolder}
						class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
						{$i18n.t('Relative path for upload directory, e.g., img/test')}
					</p>
				</div>

				<!-- 高级选项 -->
				<div class="col-span-full">
					<details class="border border-gray-200 dark:border-gray-700 rounded-lg">
						<summary
							class="px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
						>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{$i18n.t('Advanced Options')}
							</span>
						</summary>
						<div class="p-4">
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div class="flex items-center justify-between py-2">
									<div>
										<label
											for="server-compress"
											class="text-sm font-medium text-gray-900 dark:text-white"
										>
											{$i18n.t('Server Compress')}
										</label>
										<p class="text-xs text-gray-500 dark:text-gray-400">
											{$i18n.t('Compress images on server side')}
										</p>
									</div>
									<Switch id="server-compress" bind:state={imgBedConfig.serverCompress} />
								</div>

								<div class="flex items-center justify-between py-2">
									<div>
										<label for="auto-retry" class="text-sm font-medium text-gray-900 dark:text-white">
											{$i18n.t('Auto Retry')}
										</label>
										<p class="text-xs text-gray-500 dark:text-gray-400">
											{$i18n.t('Automatically retry with different channel on failure')}
										</p>
									</div>
									<Switch id="auto-retry" bind:state={imgBedConfig.autoRetry} />
								</div>

								<div>
									<label
										for="name-type"
										class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
									>
										{$i18n.t('File Naming')}
									</label>
									<Select
										id="name-type"
										bind:value={imgBedConfig.uploadNameType}
										items={nameTypeItems}
										className="w-full rounded-lg text-sm"
									/>
								</div>

								<div>
									<label
										for="return-format"
										class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
									>
										{$i18n.t('Return Format')}
									</label>
									<Select
										id="return-format"
										bind:value={imgBedConfig.returnFormat}
										items={returnFormatItems}
										className="w-full rounded-lg text-sm"
									/>
								</div>
							</div>
						</div>
					</details>
				</div>

				<div
					class="col-span-full flex justify-between items-center pt-4 border-t border-gray-100 dark:border-gray-700"
				>
					<div class="flex gap-3">
						<button
							type="button"
							class="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition"
							on:click={resetImgBedConfig}
						>
							{$i18n.t('Reset')}
						</button>
					</div>
					<div class="flex gap-3">
						<button
							type="button"
							class="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg transition"
							on:click={() => (show = false)}
						>
							{$i18n.t('Cancel')}
						</button>
						<button
							type="submit"
							class="px-4 py-2 text-sm bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50"
							disabled={!imgBedConfig.baseUrl}
						>
							{$i18n.t('Save Configuration')}
						</button>
					</div>
				</div>
			</form>

			<!-- 服务状态 -->
			<div class="flex items-center justify-between py-3 px-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
				<div>
					<span class="text-sm font-medium text-gray-900 dark:text-white">
						{$i18n.t('Service Status')}
					</span>
					<span
						class="ml-2 text-sm"
						class:text-green-600={serviceStatus}
						class:text-red-600={!serviceStatus}
					>
						{checkingStatus ? $i18n.t('Checking...') : serviceStatusText}
					</span>
				</div>
				<button
					type="button"
					class="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50"
					disabled={checkingStatus || !imgBedConfig.baseUrl}
					on:click={testImgBedConnection}
				>
					{checkingStatus ? $i18n.t('Checking...') : $i18n.t('Test Connection')}
				</button>
			</div>

			<!-- 说明信息 -->
			<div class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
				<h3 class="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
					{$i18n.t('Setup Instructions')}
				</h3>
				<ol class="text-xs text-blue-800 dark:text-blue-400 space-y-1 list-decimal list-inside">
					<li>{$i18n.t('Deploy CloudFlare ImgBed to your CloudFlare account')}</li>
					<li>{$i18n.t('Get the URL of your deployed ImgBed instance')}</li>
					<li>{$i18n.t('Enter the URL in the Base URL field above')}</li>
					<li>{$i18n.t('Add API key if your instance requires authentication')}</li>
					<li>{$i18n.t('Test the connection and save the configuration')}</li>
				</ol>
				<div class="mt-3">
					<a
						href="https://github.com/MarSeventh/CloudFlare-ImgBed"
						target="_blank"
						rel="noopener noreferrer"
						class="text-xs text-blue-600 dark:text-blue-400 hover:underline"
					>
						{$i18n.t('CloudFlare ImgBed GitHub Repository')}
					</a>
				</div>
			</div>
		</div>
	</div>
</Modal>
