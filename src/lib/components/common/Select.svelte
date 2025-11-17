<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import ChevronDown from '../icons/ChevronDown.svelte';
	import Check from '../icons/Check.svelte';

	const dispatch = createEventDispatcher();

	export let value = '';
	export let placeholder = '';
	export let className = '';
	export let disabled = false;
	export let items: Array<{ value: string; label: string }> = [];

	let isOpen = false;
	let selectedLabel = '';

	$: {
		const selectedItem = items.find(item => item.value === value);
		selectedLabel = selectedItem ? selectedItem.label : '';
	}

	const toggleDropdown = () => {
		if (!disabled) {
			isOpen = !isOpen;
		}
	};

	const selectItem = (item: { value: string; label: string }) => {
		value = item.value;
		selectedLabel = item.label;
		isOpen = false;
		dispatch('change', { value: item.value });
	};

	const handleClickOutside = (event: MouseEvent) => {
		const target = event.target as HTMLElement;
		if (!target.closest('.custom-select')) {
			isOpen = false;
		}
	};

	$: if (isOpen) {
		setTimeout(() => {
			document.addEventListener('click', handleClickOutside);
		}, 0);
	} else {
		document.removeEventListener('click', handleClickOutside);
	}
</script>

<div class="custom-select relative w-full">
	<button
		type="button"
		class={`relative w-full transition-all duration-200 ${disabled
			? 'opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800'
			: 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer border border-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20 dark:focus:ring-blue-400/20'} ${className}`}
		aria-label={placeholder || 'Select an option'}
		on:click={toggleDropdown}
		disabled={disabled}
	>
		<span class={`inline-flex w-full truncate px-3 py-2 text-sm ${className.includes('text-')
			? ''
			: 'text-gray-900 dark:text-gray-100'} ${disabled ? 'cursor-not-allowed' : ''}`}>
			{selectedLabel || placeholder}
		</span>
		<ChevronDown
			class={`absolute end-3 top-1/2 -translate-y-1/2 size-4 transition-transform duration-200 ${disabled ? 'pointer-events-none' : ''} ${isOpen ? 'rotate-180' : ''}`}
			strokeWidth="2"
		/>
	</button>

	{#if isOpen && !disabled}
		<div class="absolute z-[1100] w-full mt-1 max-h-96 overflow-y-auto rounded-xl bg-white dark:bg-gray-900 shadow-xl border border-gray-200/50 dark:border-gray-700/50 backdrop-blur-sm">
			<div class="px-1 py-1">
				{#each items as item}
					<button
						type="button"
						class={`group relative flex w-full select-none items-center rounded-lg py-2.5 pl-3 pr-8 text-sm transition-all duration-150 cursor-pointer
							${value === item.value
								? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 font-medium'
								: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}
							hover:bg-gray-100 dark:hover:bg-gray-800`}
						on:click={() => selectItem(item)}
					>
						<span class="flex-1 truncate">{item.label}</span>
						{#if value === item.value}
							<div class="absolute end-2 top-1/2 -translate-y-1/2">
								<Check class="size-4 text-blue-600 dark:text-blue-400" />
							</div>
						{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.rotate-180 {
		transform: translateY(-50%) rotate(180deg);
	}
</style>
