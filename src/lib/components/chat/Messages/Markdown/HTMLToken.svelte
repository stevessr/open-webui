<script lang="ts">
	import DOMPurify from 'dompurify';
	import type { Token } from 'marked';

	import { WEBUI_BASE_URL } from '$lib/constants';
	import Source from './Source.svelte';
	import { settings } from '$lib/stores';
	import FloatingDocPreview from '$lib/components/common/FloatingDocPreview.svelte';
	import ArrowsPointingOut from '$lib/components/icons/ArrowsPointingOut.svelte';
	import { getContext } from 'svelte';

	const i18n = getContext('i18n');

	export let id: string;
	export let token: Token;

	export let onSourceClick: Function = () => {};

	let html: string | null = null;
	let showFloatingPreview = false;
	let previewUrl = '';
	let previewTitle = 'HTML Content Preview';

	$: if (token.type === 'html' && token?.text) {
		html = DOMPurify.sanitize(token.text);
	} else {
		html = null;
	}
</script>

{#if token.type === 'html'}
	{#if html && html.includes('<video')}
		{@const video = html.match(/<video[^>]*>([\s\S]*?)<\/video>/)}
		{@const videoSrc = video && video[1]}
		{#if videoSrc}
			<!-- svelte-ignore a11y-media-has-caption -->
			<video
				class="w-full my-2"
				src={videoSrc.replaceAll('&amp;', '&')}
				title="Video player"
				frameborder="0"
				referrerpolicy="strict-origin-when-cross-origin"
				controls
				allowfullscreen
			>
				<track kind="captions" />
			</video>
		{:else}
			{token.text}
		{/if}
	{:else if html && html.includes('<audio')}
		{@const audio = html.match(/<audio[^>]*>([\s\S]*?)<\/audio>/)}
		{@const audioSrc = audio && audio[1]}
		{#if audioSrc}
			<!-- svelte-ignore a11y-media-has-caption -->
			<audio
				class="w-full my-2"
				src={audioSrc.replaceAll('&amp;', '&')}
				title="Audio player"
				controls
			></audio>
		{:else}
			{token.text}
		{/if}
	{:else if token.text && token.text.match(/<iframe\s+[^>]*src="https:\/\/www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?:\?[^"]*)?"[^>]*><\/iframe>/)}
		{@const match = token.text.match(
			/<iframe\s+[^>]*src="https:\/\/www\.youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?:\?[^"]*)?"[^>]*><\/iframe>/
		)}
		{@const ytId = match && match[1]}
		{#if ytId}
			<iframe
				class="w-full aspect-video my-2"
				src={`https://www.youtube.com/embed/${ytId}`}
				title="YouTube video player"
				frameborder="0"
				allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
				referrerpolicy="strict-origin-when-cross-origin"
				allowfullscreen
			>
			</iframe>
		{/if}
	{:else if token.text && token.text.includes('<iframe')}
		{@const match = token.text.match(/<iframe\s+[^>]*src="([^"]+)"[^>]*><\/iframe>/)}
		{@const iframeSrc = match && match[1]}
		{#if iframeSrc}
			<iframe
				class="w-full my-2"
				src={iframeSrc}
				title="Embedded content"
				frameborder="0"
				sandbox
				onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"
			></iframe>
		{:else}
			{token.text}
		{/if}
	{:else if token.text && token.text.includes('<status')}
		{@const match = token.text.match(/<status title="([^"]+)" done="(true|false)" ?\/?>/)}
		{@const statusTitle = match && match[1]}
		{@const statusDone = match && match[2] === 'true'}
		{#if statusTitle}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{statusDone === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 line-clamp-1 text-wrap"
				>
					{statusTitle}
				</div>
			</div>
		{:else}
			{token.text}
		{/if}
	{:else if token.text.includes(`<file type="html"`)}
		{@const match = token.text.match(/<file type="html" id="([^"]+)"/)}
		{@const fileId = match && match[1]}
		{#if fileId}
			<div class="relative group">
				<iframe
					class="w-full my-2"
					src={`${WEBUI_BASE_URL}/api/v1/files/${fileId}/content/html`}
					title="Content"
					frameborder="0"
					sandbox="allow-scripts allow-downloads{($settings?.iframeSandboxAllowForms ?? false)
						? ' allow-forms'
						: ''}{($settings?.iframeSandboxAllowSameOrigin ?? false) ? ' allow-same-origin' : ''}"
					referrerpolicy="strict-origin-when-cross-origin"
					allowfullscreen
					width="100%"
					onload="this.style.height=(this.contentWindow.document.body.scrollHeight+20)+'px';"
				></iframe>

				<!-- Floating Preview Button -->
				<button
					class="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200"
					on:click={() => {
						previewUrl = `${WEBUI_BASE_URL}/api/v1/files/${fileId}/content/html`;
						previewTitle = 'HTML File Preview';
						showFloatingPreview = true;
					}}
					title="Open in floating preview"
					aria-label="Open in floating preview"
				>
					<ArrowsPointingOut className="size-4" />
				</button>
			</div>
		{/if}
	{:else if token.text.includes(`<source_id`)}
		<Source {id} {token} onClick={onSourceClick} />
	{:else if html && (html.includes('<div') || html.includes('<span') || html.includes('<p') || html.includes('<h1') || html.includes('<h2') || html.includes('<h3') || html.includes('<table') || html.includes('<form'))}
		<!-- General HTML content with floating preview option -->
		<div class="relative group">
			{@html html}

			<!-- Floating Preview Button for HTML content -->
			<button
				class="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200"
				on:click={() => {
					// Create a data URL for the HTML content
					const htmlContent = `
						<!DOCTYPE html>
						<html lang="en">
						<head>
							<meta charset="UTF-8">
							<meta name="viewport" content="width=device-width, initial-scale=1.0">
							<title>HTML Preview</title>
							<style>
								body { font-family: system-ui, -apple-system, sans-serif; margin: 20px; }
							</style>
						</head>
						<body>
							${html}
						</body>
						</html>
					`;
					const blob = new Blob([htmlContent], { type: 'text/html' });
					previewUrl = URL.createObjectURL(blob);
					previewTitle = 'HTML Content Preview';
					showFloatingPreview = true;
				}}
				title="Open in floating preview"
				aria-label="Open in floating preview"
			>
				<ArrowsPointingOut className="size-4" />
			</button>
		</div>
	{:else}
		{@html html || token.text}
	{/if}
{/if}

<!-- Global Floating Preview Modal -->
{#if showFloatingPreview}
	<FloatingDocPreview
		bind:show={showFloatingPreview}
		url={previewUrl}
		title={previewTitle}
	/>
{/if}
