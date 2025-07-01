<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import { WEBUI_NAME, showSidebar, user, settings } from '$lib/stores';
	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import { page } from '$app/stores';

	const i18n = getContext('i18n');

	let loaded = false;

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
		}
		loaded = true;
	});
</script>

<svelte:head>
	<title>
		{$i18n.t('Admin Panel')} • {$WEBUI_NAME}
	</title>
</svelte:head>

{#if loaded}
	<div
		class="static left-0 flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out max-w-full relative"
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
		<nav class="   px-2.5 pt-1 backdrop-blur-xl drag-region">
			<div class=" flex items-center gap-1">
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
							class="min-w-fit p-1.5 {$page.url.pathname.includes('/admin/users')
								? ''
								: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
							href="/admin">{$i18n.t('Users')}</a
						>

						<a
							class="min-w-fit p-1.5 {$page.url.pathname.includes('/admin/evaluations')
								? ''
								: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
							href="/admin/evaluations">{$i18n.t('Evaluations')}</a
						>

						<a
							class="min-w-fit p-1.5 {$page.url.pathname.includes('/admin/functions')
								? ''
								: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
							href="/admin/functions">{$i18n.t('Functions')}</a
						>

						<a
							class="min-w-fit p-1.5 {$page.url.pathname.includes('/admin/settings')
								? ''
								: 'text-gray-300 dark:text-gray-600 hover:text-gray-700 dark:hover:text-white'} transition"
							href="/admin/settings">{$i18n.t('Settings')}</a
						>
					</div>
				</div>
			</div>
		</nav>

		<div class=" pb-1 px-[16px] flex-1 max-h-full overflow-y-auto">
			<slot />
		</div>
	</div>
{/if}
