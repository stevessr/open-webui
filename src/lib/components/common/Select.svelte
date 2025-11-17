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
		class="relative w-full {className}"
		aria-label={placeholder || 'Select an option'}
	>
		<Select.Value
			class="inline-flex w-full truncate {className.includes('text-')
				? ''
				: 'text-sm'} {disabled ? 'opacity-50 cursor-not-allowed' : ''}"
			{placeholder}
		/>
		<ChevronDown
			className="absolute end-2 top-1/2 -translate-y-1/2 size-3.5 pointer-events-none"
			strokeWidth="2.5"
		/>
	</Select.Trigger>
	<Select.Content
		class="z-50 max-h-96 overflow-y-auto rounded-lg bg-white dark:bg-gray-900 dark:text-white shadow-lg border border-gray-300/30 dark:border-gray-700/40 outline-hidden"
		transition={flyAndScale}
		sideOffset={4}
	>
		<div class="px-1 py-1">
			{#each parsedItems as item}
				<Select.Item
					class="flex w-full select-none items-center rounded-md py-2 pl-3 pr-1.5 text-sm text-gray-700 dark:text-gray-100 outline-hidden transition-all duration-75 hover:bg-gray-100 dark:hover:bg-gray-850 cursor-pointer data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-gray-850"
					value={item.value}
					label={item.label}
				>
					<span class="flex-1">{item.label}</span>
					{#if value === item.value}
						<div class="ml-auto">
							<Check />
						</div>
					{/if}
				</Select.Item>
			{/each}
		</div>
		<slot />
	</Select.Content>
</Select.Root>
