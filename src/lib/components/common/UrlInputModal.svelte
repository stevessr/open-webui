<script lang="ts">
	import Modal from '../common/Modal.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import { createEventDispatcher } from 'svelte';

	export let show = false;
	export let title = 'Enter URL';
	export let placeholder = 'Enter URL...';
	export let confirmText = 'Set';
	export let value = '';
	export let userName = '';

	const dispatch = createEventDispatcher();

	let tempValue = '';
	let inputElement;

	$: if (show) {
		tempValue = value;
		setTimeout(() => {
			inputElement?.focus();
		}, 100);
	}

	const handleConfirm = () => {
		if (tempValue && tempValue.trim()) {
			value = tempValue.trim();
			show = false;
			dispatch('submit', value);
		}
	};

	const handleCancel = () => {
		tempValue = '';
		show = false;
	};

	const handleKeydown = (e) => {
		if (e.key === 'Enter') {
			handleConfirm();
		} else if (e.key === 'Escape') {
			handleCancel();
		}
	};
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
				<ProfileImage src={tempValue.trim()} name={userName} class="w-24 h-24" alt="preview" />
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
				disabled={!tempValue || !tempValue.trim()}
				on:click={handleConfirm}
			>
				{confirmText}
			</button>
		</div>
	</div>
</Modal>
