<script>
	import { getContext, onMount } from 'svelte';
	const i18n = getContext('i18n');

	import ManageOllama from './ManageOllama.svelte';
	import Select from '$lib/components/common/Select.svelte';

	export let ollamaConfig = null;

	let selectedUrlIdx = 0;
</script>

{#if ollamaConfig}
	<div class="flex-1 mb-2.5 pr-1.5 rounded-lg bg-gray-50 dark:text-gray-300 dark:bg-gray-850">
		<Select
			className="w-full py-2 px-4 text-sm outline-hidden bg-transparent"
			bind:value={selectedUrlIdx}
			placeholder={$i18n.t('Select an Ollama instance')}
			items={ollamaConfig.OLLAMA_BASE_URLS.map((url, idx) => ({ value: idx, label: url }))}
		/>
	</div>

	<ManageOllama urlIdx={selectedUrlIdx} />
{/if}
