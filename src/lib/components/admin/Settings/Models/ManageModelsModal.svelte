<script>
	import { toast } from 'svelte-sonner';

	import { createEventDispatcher, getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { user } from '$lib/stores';

	import XMark from '$lib/components/icons/XMark.svelte';
	import Modal from '$lib/components/common/Modal.svelte';
	import ManageOllama from './Manage/ManageOllama.svelte';
	import { getOllamaConfig } from '$lib/apis/ollama';
	import Spinner from '$lib/components/common/Spinner.svelte';
	import ManageMultipleOllama from './Manage/ManageMultipleOllama.svelte';

	export let show = false;

	let selected = null;
	let ollamaConfig = null;

	onMount(async () => {
		if ($user?.role === 'admin') {
			await Promise.all([
				(async () => {
					ollamaConfig = await getOllamaConfig(localStorage.token);
				})()
			]);

			if (ollamaConfig) {
				selected = 'ollama';
				return;
			}

			selected = '';
		}
	});
</script>

<Modal size="sm" bind:show draggable={false}>
	<div>
		<div class=" flex justify-between dark:text-gray-100 px-5 pt-4">
			<div class=" text-lg font-medium self-center font-primary">
				{$i18n.t('Manage Models')}
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col md:flex-row w-full px-3 pb-4 md:space-x-4 dark:text-gray-200">
			<div class=" flex flex-col w-full sm:flex-row sm:justify-center sm:space-x-6">
				{#if selected === ''}
					<div class=" py-5 text-gray-400 text-xs">
						<div>
							{$i18n.t('No inference engine with management support found')}
						</div>
					</div>
				{:else if selected !== null}
					<div class=" flex w-full flex-col">
						<div
							class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium rounded-full bg-transparent dark:text-gray-200"
						>
							<button
								class="min-w-fit p-1.5 {selected === 'ollama'
									? ''
									: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
								on:click={() => {
									selected = 'ollama';
								}}>{$i18n.t('Ollama')}</button
							>

							<!-- <button
								class="min-w-fit p-1.5 {selected === 'llamacpp'
									? ''
									: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
								on:click={() => {
									selected = 'llamacpp';
								}}>{$i18n.t('Llama.cpp')}</button
							> -->
						</div>

						<div class=" px-1.5 py-1">
							{#if selected === 'ollama'}
								<ManageMultipleOllama {ollamaConfig} />
							{/if}
						</div>
					</div>
				{:else}
					<div class=" py-5">
						<Spinner />
					</div>
				{/if}
			</div>
		</div>
	</div>
</Modal>
