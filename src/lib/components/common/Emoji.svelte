<script>
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { shortCodesToEmojis } from '$lib/stores';
	import ProfileImage from './ProfileImage.svelte';

	export let shortCode;
	export let className = 'size-4';
</script>

{#if $shortCodesToEmojis[shortCode]}
	<ProfileImage
		src="{WEBUI_BASE_URL}/assets/emojis/{$shortCodesToEmojis[shortCode].toLowerCase()}.svg"
		alt={shortCode}
		class={className}
	/>
{:else}
	<div>
		{shortCode}
	</div>
{/if}
