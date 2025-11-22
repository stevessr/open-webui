<script lang="ts">
	import { onMount } from 'svelte';

	export let options: Array<{ value: string; label?: string }> = [];
	export let value: string = '';
	export let placeholder: string = '';
	export let ariaLabel: string = '';
	export let listId: string = '';
	export let onSelect: (value: string) => void = () => {};
	export let onKeydown: (event: KeyboardEvent) => void = () => {};
	export let className: string = '';

	let show = false;
	let inputElement: HTMLInputElement;

	$: filteredOptions = options.filter((option) =>
		option.value.toLowerCase().includes(value.toLowerCase())
	);

	const handleSelect = (selectedValue: string) => {
		value = selectedValue;
		show = false;
		onSelect(selectedValue);
	};

	const handleInputChange = (event: Event) => {
		const target = event.target as HTMLInputElement;
		value = target.value;
		if (filteredOptions.length > 0 && !show) {
			show = true;
		}
	};

	const handleInputClick = () => {
		if (filteredOptions.length > 0) {
			show = !show;
		}
	};

	const handleInputKeydown = (event: KeyboardEvent) => {
		if (event.key === 'ArrowDown') {
			event.preventDefault();
			show = true;
		} else if (event.key === 'Enter') {
			if (show && filteredOptions.length > 0) {
				event.preventDefault();
				handleSelect(filteredOptions[0].value);
			} else {
				onKeydown(event);
			}
		} else if (event.key === 'Escape') {
			show = false;
		} else {
			onKeydown(event);
		}
	};

	const handleOutsideClick = (event: MouseEvent) => {
		if (inputElement && !inputElement.contains(event.target as Node)) {
			show = false;
		}
	};

	const handleBlur = () => {
		setTimeout(() => {
			show = false;
		}, 150);
	};

	onMount(() => {
		document.addEventListener('click', handleOutsideClick);
		return () => {
			document.removeEventListener('click', handleOutsideClick);
		};
	});
</script>

<div class="relative">
	<input
		bind:this={inputElement}
		type="text"
		class="w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 {className}"
		{placeholder}
		aria-label={ariaLabel}
		bind:value
		on:input={handleInputChange}
		on:click={handleInputClick}
		on:keydown={handleInputKeydown}
		on:blur={handleBlur}
		role="combobox"
		aria-expanded={show}
		aria-autocomplete="list"
		aria-controls="data-list-dropdown"
		on:click|stopPropagation
	/>

	{#if show}
		<div
			class="transv2 absolute top-full mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto z-50"
			id="data-list-dropdown"
			role="listbox"
			tabindex="-1"
		>
			{#if filteredOptions.length > 0}
				<div class="py-1">
					{#each filteredOptions as option, index}
						<button
							type="button"
							class="w-full px-3 py-2 cursor-pointer hover:bg-gray-100 text-sm text-left"
							on:click={() => handleSelect(option.value)}
							on:keydown={(event) => {
								if (event.key === 'Enter' || event.key === ' ') {
									event.preventDefault();
									handleSelect(option.value);
								}
							}}
							role="option"
							tabindex="0"
							aria-selected={value === option.value}
						>
							{option.label || option.value}
						</button>
					{/each}
				</div>
			{:else}
				<div class="px-3 py-2 text-sm text-gray-500">
					{value ? 'No options found' : 'Type to search'}
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	div {
		position: relative;
	}
</style>
