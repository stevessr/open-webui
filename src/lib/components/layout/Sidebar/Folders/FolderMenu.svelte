<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { flyAndScale } from '$lib/utils/transitions';
	import { createEventDispatcher, getContext } from 'svelte';
	import type { Writable } from 'svelte/store';
	import type { i18n as i18nType } from 'i18next';
	const i18n = getContext<Writable<i18nType>>('i18n');

	const dispatch = createEventDispatcher();

	import Dropdown from '$lib/components/common/Dropdown.svelte';
	import GarbageBin from '$lib/components/icons/GarbageBin.svelte';
	import Pencil from '$lib/components/icons/Pencil.svelte';
	import Download from '$lib/components/icons/Download.svelte';
	import PencilSquare from '$lib/components/icons/PencilSquare.svelte';

	export let align: 'start' | 'end' = 'start';
	export let onEdit = () => {};
	export let onExport = () => {};
	export let onDelete = () => {};

	export let align: 'start' | 'end' = 'start';
	export let onEdit = () => {};
	export let onExport = () => {};
	export let onDelete = () => {};

	let show = false;
</script>

<Dropdown
	bind:show
	on:change={(e) => {
		if (e.detail === false) {
			dispatch('close');
		}
	}}
>
	<DropdownMenu.Trigger asChild let:builder>
		<slot {builder} />
	</DropdownMenu.Trigger>
	<div slot="content">
		<DropdownMenu.Content
			class="w-full max-w-[170px] rounded-lg px-1 py-1.5  z-50 bg-white dark:bg-gray-850 dark:text-white shadow-lg"
			sideOffset={-2}
			side="bottom"
			{align}
			transition={flyAndScale}
		>
			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-1.5 text-sm  cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					onEdit();
				}}
			>
				<Pencil strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Edit')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex gap-2 items-center px-3 py-1.5 text-sm  cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					onExport();
				}}
			>
				<Download strokeWidth="2" />

				<div class="flex items-center">{$i18n.t('Export')}</div>
			</DropdownMenu.Item>

			<DropdownMenu.Item
				class="flex  gap-2  items-center px-3 py-1.5 text-sm  cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 rounded-md"
				on:click={() => {
					onDelete();
				}}
			>
				<GarbageBin strokeWidth="2" />
				<div class="flex items-center">{$i18n.t('Delete')}</div>
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</div>
</Dropdown>
