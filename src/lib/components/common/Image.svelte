<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	import { settings } from '$lib/stores';
	import ImagePreview from './ImagePreview.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import { getContext, onMount } from 'svelte';
	import type { i18n as i18nInstance } from 'i18next';

	export let src = '';
	export let alt = '';
	export let lazy = true;

	export let className = ` w-full ${($settings?.highContrastMode ?? false) ? '' : 'outline-hidden focus:outline-hidden'}`;

	export let imageClassName = 'rounded-lg';

	export let dismissible = false;
	export let onDismiss = () => {};

	const i18n = getContext<i18nInstance>('i18n');

	let _src = '';
	$: _src = src.startsWith('/') ? `${WEBUI_BASE_URL}${src}` : src;

	const showImagePreviewLabel = i18n?.t('Show image preview');
	const removeImageLabel = i18n?.t('Remove image');

	let showImagePreview = false;
	let containerElement: HTMLElement;
	let isInView = false;

	// Lazy loading with Intersection Observer
	onMount(() => {
		if (!lazy) {
			isInView = true;
			return;
		}

		if (!containerElement) return;

		const observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					if (entry.isIntersecting) {
						isInView = true;
						observer.unobserve(containerElement);
					}
				});
			},
			{
				rootMargin: '50px' // Start loading 50px before the image comes into view
			}
		);

		observer.observe(containerElement);

		return () => {
			observer.disconnect();
		};
	});

	// Determine the actual src to use
	$: actualSrc = lazy ? (isInView ? _src : '') : _src;
</script>

<ImagePreview bind:show={showImagePreview} src={_src} {alt} />

<div class=" relative group w-fit" bind:this={containerElement}>
	<button
		class={className}
		on:click={() => {
			showImagePreview = true;
		}}
		aria-label={showImagePreviewLabel}
		type="button"
	>
		{#if actualSrc}
			<img src={actualSrc} {alt} class={imageClassName} draggable="false" data-cy="image" />
		{:else}
			<!-- Placeholder while lazy loading -->
			<div
				class="{imageClassName} bg-gray-200 dark:bg-gray-700 animate-pulse flex items-center justify-center min-h-[100px]"
			>
				<svg class="w-8 h-8 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
					<path
						fill-rule="evenodd"
						d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
						clip-rule="evenodd"
					/>
				</svg>
			</div>
		{/if}
	</button>

	{#if dismissible}
		<div class=" absolute -top-1 -right-1">
			<button
				aria-label={removeImageLabel}
				class=" bg-white text-black border border-white rounded-full group-hover:visible invisible transition"
				type="button"
				on:click={() => {
					onDismiss();
				}}
			>
				<XMark className={'size-4'} />
			</button>
		</div>
	{/if}
</div>
