<script>
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { shortCodesToEmojis } from '$lib/stores';

	export let shortCode;
	export let className = 'size-4';
</script>

{#if shortCode.startsWith('/') || shortCode.startsWith('http')}
	<img src={shortCode} alt={shortCode} class={className} loading="lazy" />
{:else if $shortCodesToEmojis[shortCode]}
	<img
		src="{WEBUI_BASE_URL}/assets/emojis/{$shortCodesToEmojis[shortCode].toLowerCase()}.svg"
		alt={shortCode}
		class={className}
		loading="lazy"
	/>
{:else}
	<div>
		{shortCode}
	</div>
{/if}
