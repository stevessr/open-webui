<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	import { settings } from '$lib/stores';
	import ImagePreview from './ImagePreview.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import ProfileImage from './ProfileImage.svelte';
	import { getContext } from 'svelte';

	export let src = '';
	export let alt = '';

	export let className = ` w-full ${($settings?.highContrastMode ?? false) ? '' : 'outline-hidden focus:outline-hidden'}`;

	export let imageClassName = 'rounded-lg';

	export let dismissible = false;
	export let onDismiss = () => {};

	const i18n = getContext('i18n');
	let helper: string = '';
	$: helper = src.startsWith('/') ? `${WEBUI_BASE_URL}${src}` : src;

	let _src = '';
	$: _src = src.includes('api/v1/files') ? `${src}/content` : src;

	let showImagePreview = false;
	let isVideo = false;

	$: isVideo =
		_src &&
		['.mp4', '.webm', '.ogg', '.avi', '.mov', '.wmv', '.flv', '.m4v'].some((ext) =>
			_src.toLowerCase().includes(ext)
		);
</script>

<ImagePreview bind:show={showImagePreview} src={_src} {alt} />

<div class=" relative group w-fit flex items-center">
	<button
		class={className}
		on:click={() => {
			if (!isVideo) {
				showImagePreview = true;
			}
		}}
		aria-label={isVideo ? $i18n.t('Video content') : $i18n.t('Show image preview')}
		type="button"
	>
		{#if isVideo}
			<video src={_src} class={imageClassName} controls data-cy="video" title={alt} autoplay muted
			></video>
		{:else}
			<ProfileImage src={_src} class={imageClassName} {alt} />
		{/if}
	</button>

	{#if dismissible}
		<div class=" absolute -top-1 -right-1">
			<button
				aria-label={$i18n.t('Remove image')}
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
