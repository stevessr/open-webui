<script lang="ts">
	import { Select } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher } from 'svelte';
	import ChevronDown from '../icons/ChevronDown.svelte';
	import Check from '../icons/Check.svelte';

	const dispatch = createEventDispatcher();

	export let value = '';
	export let placeholder = '';
	export let className = '';
	export let disabled = false;

	// For compatibility with native select, we'll accept slot content for options
	// But also support items prop for programmatic usage
	export let items: Array<{ value: string; label: string }> = [];

	// Parse options from slot if items not provided
	let parsedItems: Array<{ value: string; label: string }> = [];

	$: {
		if (items.length > 0) {
			parsedItems = items;
		}
	}

	$: selectedItem = parsedItems.find((item) => item.value === value) || null;
</script>

<Select.Root
	{disabled}
	items={parsedItems}
	selected={selectedItem}
	onSelectedChange={(selected) => {
		if (selected) {
			value = selected.value;
			dispatch('change', { value: selected.value });
		}
	}}
>
	<Select.Trigger
		class={`relative w-full transition-all duration-200 ${disabled
			? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800'
			: 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer border border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20'} ${className}`}
		aria-label={placeholder || 'Select an option'}
	>
		<Select.Value
			class={`inline-flex w-full truncate px-3 py-2 text-sm ${className.includes('text-')
				? ''
				: 'text-gray-900 dark:text-gray-100'} ${disabled ? 'cursor-not-allowed' : ''}`}
			{placeholder}
		/>
		<ChevronDown
			class={`absolute end-3 top-1/2 -translate-y-1/2 size-4 transition-transform duration-200 ${disabled ? 'pointer-events-none' : 'group-open:rotate-180'}`}
			strokeWidth="2"
		/>
	</Select.Trigger>
	<Select.Content
		class="z-50 max-h-96 overflow-y-auto rounded-xl bg-white dark:bg-gray-900 shadow-xl border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm outline-hidden"
		transition={flyAndScale}
		sideOffset={4}
	>
		<div class="px-1 py-1">
			{#each parsedItems as item}
				<Select.Item
					class={`group relative flex w-full select-none items-center rounded-lg py-2.5 pl-3 pr-8 text-sm transition-all duration-150 cursor-pointer
						${value === item.value
							? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}
						data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-gray-800
						data-[highlighted]:text-gray-900 dark:data-[highlighted]:text-gray-100`}
					value={item.value}
					label={item.label}
				>
					<span class="flex-1 truncate">{item.label}</span>
					{#if value === item.value}
						<div class="absolute end-2 top-1/2 -translate-y-1/2">
							<Check class="size-4 text-blue-600 dark:text-blue-400" />
						</div>
					{/if}
				</Select.Item>
			{/each}
		</div>
		<slot />
	</Select.Content>
</Select.Root>
