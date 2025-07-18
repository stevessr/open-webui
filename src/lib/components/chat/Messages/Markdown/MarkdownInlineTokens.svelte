<script lang="ts">
	import DOMPurify from 'dompurify';

	import type { Token } from 'marked';

	const i18n = getI18n();

	import Image from '$lib/components/common/Image.svelte';
	import KatexRenderer from './KatexRenderer.svelte';
	import Source from './Source.svelte';
	import HtmlToken from './HTMLToken.svelte';
	import { getI18n } from '$lib/i18n/helpers';

	export let id: string;
	export let tokens: Token[];
	export let onSourceClick: Function = () => {};
</script>

{#each tokens as token}
	{#if token.type === 'escape'}
		{unescapeHtml(token.text)}
	{:else if token.type === 'html'}
		<HtmlToken {id} {token} {onSourceClick} />
	{:else if token.type === 'link'}
		{#if token.tokens}
			<a href={token.href} target="_blank" rel="nofollow" title={token.title}>
				<svelte:self id={`${id}-a`} tokens={token.tokens} {onSourceClick} />
			</a>
		{:else}
			<a href={token.href} target="_blank" rel="nofollow" title={token.title}>{token.text}</a>
		{/if}
	{:else if token.type === 'image'}
		<Image src={token.href} alt={token.text} />
	{:else if token.type === 'strong'}
		<strong><svelte:self id={`${id}-strong`} tokens={token.tokens} {onSourceClick} /></strong>
	{:else if token.type === 'em'}
		<em><svelte:self id={`${id}-em`} tokens={token.tokens} {onSourceClick} /></em>
	{:else if token.type === 'codespan'}
		<code
			class="codespan cursor-pointer"
			on:click={() => {
				copyToClipboard(unescapeHtml(token.text));
				toast.success($i18n.t('Copied to clipboard'));
			}}>{unescapeHtml(token.text)}</code
		>
	{:else if token.type === 'br'}
		<br />
	{:else if token.type === 'del'}
		<del><svelte:self id={`${id}-del`} tokens={token.tokens} {onSourceClick} /></del>
	{:else if token.type === 'inlineKatex'}
		{#if token.text}
			<KatexRenderer content={token.text} displayMode={false} />
		{/if}
	{:else if token.type === 'iframe'}
		<iframe
			src="{WEBUI_BASE_URL}/api/v1/files/{token.fileId}/content"
			title={token.fileId}
			width="100%"
			frameborder="0"
			onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"
		></iframe>
	{:else if token.type === 'text'}
		{token.raw}
	{/if}
{/each}
