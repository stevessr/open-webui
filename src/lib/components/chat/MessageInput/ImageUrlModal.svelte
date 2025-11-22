<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, getContext } from 'svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';

	const dispatch = createEventDispatcher();
	const i18n = getContext('i18n');

	export let show = false;
	export let onSubmit = (imageUrl: string) => {};

	let imageUrl = '';
	let imagePreview = '';
	let isValidUrl = false;
	let isLoading = false;

	// 验证 URL 并加载预览
	const validateAndPreview = async () => {
		console.log('validateAndPreview called with imageUrl:', imageUrl);

		if (!imageUrl.trim()) {
			isValidUrl = false;
			imagePreview = '';
			console.log('Empty URL, marking as invalid');
			return;
		}

		try {
			new URL(imageUrl);
			isValidUrl = true;
			console.log('URL format is valid');

			// 检查是否为图片 URL（支持更多图片格式）
			const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg|bmp|ico|jfif|tiff?|avif|heic)$/i;
			if (imageUrl.match(imageExtensions)) {
				console.log('URL matches image extension, attempting preview');
				isLoading = true;
				imagePreview = imageUrl;

				// 测试图片是否可加载
				const img = new Image();
				img.crossOrigin = 'anonymous'; // 尝试允许跨域加载

				img.onload = () => {
					isLoading = false;
					console.log('Image preview loaded successfully');
				};

				img.onerror = () => {
					isLoading = false;
					// 不清空 imagePreview，仍然显示用户输入的 URL
					// 只是标记预览失败，但 URL 本身可能是有效的
					console.warn(
						'Image preview failed to load (possibly due to CORS), but URL may still be valid'
					);
					// 不显示错误 toast，因为这可能只是 CORS 问题
				};

				img.src = imageUrl;
			} else if (imageUrl.endsWith('content') && imageUrl.match('api/v1/files')) {
				// 处理特殊的 content 结尾情况
				console.log('URL ends with "content", attempting preview');
				isLoading = true;
				imagePreview = imageUrl;

				const img = new Image();
				img.crossOrigin = 'anonymous';

				img.onload = () => {
					isLoading = false;
					console.log('Image preview loaded successfully for content URL');
				};

				img.onerror = () => {
					isLoading = false;
					console.warn('Image preview failed to load for content URL');
				};

				img.src = imageUrl;
			} else {
				imagePreview = '';
				console.log('URL does not match image extensions');
			}
		} catch (error) {
			console.warn('URL validation failed:', error);
			isValidUrl = false;
			imagePreview = '';
		}
	};

	const handleSubmit = () => {
		if (!isValidUrl) {
			toast.error($i18n.t('Please enter a valid image URL'));
			return;
		}

		// 检查是否为图片 URL（支持更多图片格式）
		const imageExtensions = /\.(jpg|jpeg|png|gif|webp|svg|bmp|ico|jfif|tiff?|avif|heic)$/i;
		if (!imageUrl.match(imageExtensions)) {
			toast.error($i18n.t('URL must point to an image file'));
			return;
		}

		console.log('Submitting image URL:', imageUrl);
		onSubmit(imageUrl);
		imageUrl = '';
		imagePreview = '';
		isValidUrl = false;
		show = false;
	};

	const handleCancel = () => {
		imageUrl = '';
		imagePreview = '';
		isValidUrl = false;
		show = false;
	};

	$: validateAndPreview();
</script>

<Modal size="sm" bind:show>
	<div>
		<div class="flex justify-between dark:text-gray-100 px-5 pt-4 pb-1.5">
			<h1 class="text-lg font-medium self-center font-primary">
				{$i18n.t('Add Image URL')}
			</h1>
			<button class="self-center" aria-label={$i18n.t('Close modal')} on:click={handleCancel}>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col md:flex-row w-full px-4 pb-4 md:space-x-4 dark:text-gray-200">
			<div class="flex flex-col w-full sm:flex-row sm:justify-center sm:space-x-6">
				<form
					class="flex flex-col w-full px-1 space-y-4"
					on:submit={(e) => {
						e.preventDefault();
						handleSubmit();
					}}
				>
					<div>
						<label
							for="image-url"
							class="block text-sm font-medium text-gray-900 dark:text-white mb-2"
						>
							{$i18n.t('Image URL')}
						</label>
						<input
							id="image-url"
							type="url"
							placeholder="https://example.com/image.jpg"
							bind:value={imageUrl}
							on:input={() => {
								console.log('Input event triggered, imageUrl:', imageUrl);
								validateAndPreview();
							}}
							class="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
						<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
							{$i18n.t('Enter the URL of an image file (JPG, PNG, GIF, WebP, etc.)')}
						</p>
					</div>

					<!-- 图片预览 -->
					{#if imagePreview}
						<div>
							<label class="block text-sm font-medium text-gray-900 dark:text-white mb-2">
								{$i18n.t('Preview')}
							</label>
							<div
								class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden relative"
							>
								<img
									src={imagePreview}
									alt="Image preview"
									class="w-full h-48 object-contain bg-gray-50 dark:bg-gray-800"
									class:opacity-50={isLoading}
								/>
								{#if isLoading}
									<div
										class="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-gray-800"
									>
										<div class="flex flex-col items-center space-y-2">
											<div
												class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"
											></div>
											<div class="text-sm text-gray-600 dark:text-gray-400">
												{$i18n.t('Loading preview...')}
											</div>
										</div>
									</div>
								{/if}
							</div>
						</div>
					{/if}

					<!-- URL 验证状态 -->
					{#if imageUrl && !isValidUrl}
						<div
							class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
						>
							<p class="text-sm text-red-600 dark:text-red-400">
								{$i18n.t('Please enter a valid URL')}
							</p>
						</div>
					{/if}

					<div
						class="flex justify-between items-center pt-4 border-t border-gray-100 dark:border-gray-700"
					>
						<div class="flex gap-3">
							<button
								type="button"
								class="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 rounded-lg transition"
								on:click={handleCancel}
							>
								{$i18n.t('Cancel')}
							</button>
						</div>
						<div class="flex gap-3">
							<button
								type="submit"
								class="px-4 py-2 text-sm bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50"
								disabled={!isValidUrl || isLoading}
							>
								{$i18n.t('Add Image')}
							</button>
						</div>
					</div>
				</form>
			</div>
		</div>
	</div>
</Modal>
