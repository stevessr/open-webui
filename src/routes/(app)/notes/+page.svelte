<script>
	import { showArchivedChats, showSidebar, user, settings } from '$lib/stores';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	import MenuLines from '$lib/components/icons/MenuLines.svelte';
	import UserMenu from '$lib/components/layout/Sidebar/UserMenu.svelte';
	import Notes from '$lib/components/notes/Notes.svelte';
</script>

<div
	class=" flex flex-col w-full h-screen max-h-[100dvh] transition-width duration-200 ease-in-out  max-w-full relative"
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
	<nav class="   px-2 pt-1 backdrop-blur-xl w-full drag-region">
		<div class=" flex items-center">
			<div class="{$showSidebar ? 'md:hidden' : ''} flex flex-none items-center">
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

			<div class="ml-2 py-0.5 self-center flex items-center justify-between w-full">
				<div class="">
					<div
						class="flex gap-1 scrollbar-none overflow-x-auto w-fit text-center text-sm font-medium bg-transparent py-1 touch-auto pointer-events-auto"
					>
						<a class="min-w-fit transition" href="/notes">
							{$i18n.t('Notes')}
						</a>
					</div>
				</div>

				<div class=" self-center flex items-center gap-1">
					{#if $user !== undefined && $user !== null}
						<UserMenu
							className="max-w-[240px]"
							role={$user?.role}
							help={true}
							on:show={(e) => {
								if (e.detail === 'archived-chat') {
									showArchivedChats.set(true);
								}
							}}
						>
							<button
								class="select-none flex rounded-xl p-1.5 w-full hover:bg-gray-50 dark:hover:bg-gray-850 transition"
								aria-label="User Menu"
							>
								<div class=" self-center">
									<img
										src={$user?.profile_image_url}
										class="size-6 w-auto object-cover rounded-full"
										alt="User profile"
										draggable="false"
									/>
								</div>
							</button>
						</UserMenu>
					{/if}
				</div>
			</div>
		</div>
	</nav>

	<div class=" pb-1 flex-1 max-h-full overflow-y-auto @container">
		<Notes />
	</div>
</div>
