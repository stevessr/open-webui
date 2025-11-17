<script lang="ts">
	import { getContext } from 'svelte';

	import { generateInitialsImage, isVideoUrl } from '$lib/utils';

	const i18n = getContext('i18n');

	export let src = '';
	export let name = '';
	export let className = '';
	export let alt = 'profile';
	export let autoplay = true;
	export let muted = true;
	export let loop = true;
</script>

{#if src && isVideoUrl(src)}
	<video
		src={src}
		{alt}
		class="rounded-full {className} object-cover"
		{autoplay}
		{muted}
		{loop}
	></video>
{:else}
	<img
		src={src !== '' ? src : generateInitialsImage(name)}
		{alt}
		class="rounded-full {className} object-cover"
	/>
{/if}