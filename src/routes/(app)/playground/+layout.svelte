<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { WEBUI_NAME, showSidebar, functions, settings } from '$lib/stores';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { page } from '$app/stores';

	const i18n = getContext('i18n');

	onMount(async () => {});
</script>

<svelte:head>
	<title>
		{$i18n.t('Playground')} • {$WEBUI_NAME}
	</title>
</svelte:head>

<div
	class="static flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out  max-w-full relative"
>
	<!-- Custom Background Support -->
	{#if $settings?.backgroundImageUrl ?? null}
		{#if $settings?.backgroundImageUrl?.endsWith('.mp4')}
			<!-- Video background -->
			<video
				class="absolute top-0 left-0 w-full h-full object-cover z-[-1]"
				src={$settings.backgroundImageUrl}
				autoplay
				muted
				loop
				playsinline
			>
				<track kind="captions" />
			</video>
		{:else}
			<!-- Image background -->
			<div
				class="absolute top-0 left-0 w-full h-full bg-cover bg-center bg-no-repeat z-[-1]"
				style="background-image: url({$settings.backgroundImageUrl})"
			/>
		{/if}
	{/if}
	<nav class="   px-2.5 pt-1 backdrop-blur-xl w-full drag-region">
		<div class=" flex items-center">
			<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center self-end">
				<button
					id="sidebar-toggle-button"
					class="cursor-pointer p-1.5 flex rounded-xl hover:bg-gray-100 dark:hover:bg-gray-850 transition"
					on:click={() => {
						showSidebar.set(!$showSidebar);
					}}
					aria-label="Toggle Sidebar"
				>
					<div class=" m-auto self-center">
						<MenuLines />
					</div>
				</button>
			</div>

			<div class=" flex w-full">
				<div
					class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium rounded-full bg-transparent pt-1"
				>
					<a
						class="min-w-fit p-1.5 {['/playground', '/playground/'].includes($page.url.pathname)
							? ''
							: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
						href="/playground">{$i18n.t('Chat')}</a
					>

					<!-- <a
						class="min-w-fit p-1.5 {$page.url.pathname.includes('/playground/notes')
							? ''
							: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
						href="/playground/notes">{$i18n.t('Notes')}</a
					> -->

					<a
						class="min-w-fit p-1.5 {$page.url.pathname.includes('/playground/completions')
							? ''
							: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
						href="/playground/completions">{$i18n.t('Completions')}</a
					>
				</div>
			</div>
		</div>
	</nav>

	<div class=" flex-1 max-h-full overflow-y-auto">
		<slot />
	</div>
</div>
