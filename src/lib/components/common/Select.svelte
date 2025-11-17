<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { DropdownMenu } from 'bits-ui';
	import ChevronDown from '../icons/ChevronDown.svelte';
	import Check from '../icons/Check.svelte';

	const dispatch = createEventDispatcher();

	export let value = '';
	export let placeholder = '';
	export let className = '';
	export let disabled = false;
	export let items: Array<{ value: string; label: string; disabled?: boolean }> = [];

	let show = false;

	$: selectedLabel = items.find((item) => item.value === value)?.label || '';

	const handleSelect = (selectedValue: string) => {
		console.log('handleSelect called with:', selectedValue);
		value = selectedValue;
		show = false;
		dispatch('change', { value: selectedValue });
	};
</script>

<DropdownMenu.Root bind:open={show} {disabled}>
	<DropdownMenu.Trigger
		class="trans relative w-full transition-all duration-200 {disabled
			? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800'
			: 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer border border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20'} {className}"
		aria-label={placeholder || 'Select an option'}
		{disabled}
	>
		<span
			class="inline-flex w-full truncate px-3 py-2 text-sm {className.includes('text-')
				? ''
				: 'text-gray-900 dark:text-gray-100'} {disabled ? 'cursor-not-allowed' : ''}"
		>
			{selectedLabel || placeholder}
		</span>
		<ChevronDown
			class="absolute end-3 top-1/2 -translate-y-1/2 size-4 transition-transform duration-200 {disabled
				? 'pointer-events-none'
				: ''} {show ? 'rotate-180' : ''}"
			strokeWidth="2"
		/>
	</DropdownMenu.Trigger>

	<DropdownMenu.Content
		class="transv2 z-2999 w-full max-w-sm rounded-2xl bg-white dark:bg-gray-900 shadow-2xl border border-gray-200/50 dark:border-gray-700/50 max-h-[80vh] overflow-hidden"
		side="bottom"
		sideOffset={4}
		align="start"
	>
		<div class="p-4 border-b border-gray-200 dark:border-gray-700">
			<h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
				{placeholder || '选择选项'}
			</h3>
		</div>

		<div class="max-h-60 overflow-y-auto">
			<div class="p-2">
				{#each items as item}
					<DropdownMenu.Item
						class="group relative flex w-full select-none items-center rounded-lg py-3 px-4 text-sm transition-all duration-150 cursor-pointer mb-1 {value ===
						item.value
							? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'} {item.disabled
							? 'opacity-50 cursor-not-allowed'
							: ''}"
						disabled={item.disabled}
						on:click={() => {
							if (!item.disabled) {
								console.log('Item clicked:', item);
								handleSelect(item.value);
							}
						}}
					>
						<span class="flex-1 truncate">{item.label}</span>
						{#if value === item.value}
							<div class="ml-2">
								<Check class="size-5 text-blue-600 dark:text-blue-400" />
							</div>
						{/if}
					</DropdownMenu.Item>
				{/each}
			</div>
		</div>
	</DropdownMenu.Content>
</DropdownMenu.Root>

<style>
	.rotate-180 {
		transform: translateY(-50%) rotate(180deg);
	}
</style>
