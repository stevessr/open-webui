<script lang="ts">
	import Modal from '../common/Modal.svelte';
	import { createEventDispatcher } from 'svelte';
	import { isVideoUrl } from '$lib/utils';

	export let show = false;
	export let title = 'Enter URL';
	export let placeholder = 'Enter URL...';
	export let confirmText = 'Set';
	export let value = '';

	const dispatch = createEventDispatcher();

	let tempValue = '';
	let inputElement;
	let previewError = '';

	$: if (show) {
		tempValue = value;
		previewError = '';
		setTimeout(() => {
			inputElement?.focus();
		}, 100);
	}

	const handleConfirm = () => {
		if (tempValue && tempValue.trim()) {
			value = tempValue.trim();
			show = false;
			dispatch('confirm');
		}
	};

	const handleCancel = () => {
		tempValue = '';
		previewError = '';
		show = false;
	};

	const handleKeydown = (e) => {
		if (e.key === 'Enter') {
			handleConfirm();
		} else if (e.key === 'Escape') {
			handleCancel();
		}
	};

	const handleMediaError = () => {
		previewError = 'Failed to load media';
	};

	const handleMediaLoad = () => {
		previewError = '';
	};

	$: isVideo = tempValue && tempValue.trim() && isVideoUrl(tempValue.trim());
</script>

<Modal bind:show size="sm" className="bg-white dark:bg-gray-800 rounded-lg">
	<div class="p-6">
		<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
			{title}
		</h3>

		<input
			bind:this={inputElement}
			bind:value={tempValue}
			type="url"
			{placeholder}
			class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
			on:keydown={handleKeydown}
		/>

		{#if tempValue && tempValue.trim()}
			<div class="mt-4 flex flex-col items-center">
				<div class="text-sm text-gray-600 dark:text-gray-400 mb-2">Preview:</div>
				{#if previewError}
					<div class="text-sm text-red-500 mb-2">{previewError}</div>
				{/if}
				{#if isVideo}
					<video
						src={tempValue.trim()}
						alt="preview"
						class="max-w-full max-h-48 w-auto h-auto object-contain rounded-lg border border-gray-200 dark:border-gray-600"
						on:error={handleMediaError}
						on:loadeddata={handleMediaLoad}
						controls
						muted
					/>
				{:else}
					<img
						src={tempValue.trim()}
						alt="preview"
						class="max-w-full max-h-48 w-auto h-auto object-contain rounded-lg border border-gray-200 dark:border-gray-600"
						on:error={handleMediaError}
						on:load={handleMediaLoad}
					/>
				{/if}
			</div>
		{/if}

		<div class="flex justify-end gap-3 mt-4">
			<button
				class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 transition"
				on:click={handleCancel}
			>
				Cancel
			</button>
			<button
				class="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
				disabled={!tempValue || !tempValue.trim() || previewError !== ''}
				on:click={handleConfirm}
			>
				{confirmText}
			</button>
		</div>
	</div>
</Modal>
