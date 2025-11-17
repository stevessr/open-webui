<script lang="ts">
	import { isVideoUrl } from '$lib/utils/index';

	export let src: string = '';
	export let alt: string = '';
	export let className: string = '';
	export let crossOrigin: string | null = null;
	export let controls: boolean = true;
	export let autoplay: boolean = false;
	export let muted: boolean = false;
	export let loop: boolean = false;

	$: isVideo = src && isVideoUrl(src);
</script>

{#if isVideo}
	<video
		{src}
		{controls}
		{autoplay}
		{muted}
		{loop}
		class={className}
		crossorigin={crossOrigin}
		data-cy="video"
		title={alt}
	>
		Your browser does not support the video tag.
	</video>
{:else}
	<img
		{src}
		{alt}
		class={className}
		crossorigin={crossOrigin}
		draggable="false"
		data-cy="image"
	/>
{/if}