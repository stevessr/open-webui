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

	const isVideo = (url: string) => {
		if (!url) return false;
		const u = url.toLowerCase();
		if (u.startsWith('data:video/') || u.startsWith('blob:')) return true;
		return ['.mp4', '.webm', '.ogg', '.ogv', '.mov', '.m4v', '.avi', '.mkv'].some((ext) => u.endsWith(ext));
	};
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
		{#if isVideo(_src)}
			<!-- svelte-ignore a11y-media-caption -->
			<video src={_src} aria-label={alt} class={imageClassName} controls draggable="false" data-cy="video">
				<track kind="captions" src="" />
			</video>
		{:else}
			<img src={_src} {alt} class={imageClassName} draggable="false" data-cy="image" />
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
