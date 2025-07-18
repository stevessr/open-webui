<script lang="ts">

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/favicon.png`;

	$: finalSrc =
		src === ''
			? `${WEBUI_BASE_URL}/static/favicon.png`
			: src.startsWith(WEBUI_BASE_URL) ||
				  src.startsWith('https://www.gravatar.com/avatar/') ||
				  src.startsWith('data:') ||
				  src.startsWith('/')
				? src
				: `/user.gif`;

	$: isVideo = finalSrc.toLowerCase().endsWith('.mp4');
</script>

{#if isVideo}
	<video
		src={finalSrc}
		class=" {className} object-cover rounded-full -translate-y-[1px]"
		autoplay
		muted
		loop
		playsinline
		draggable="false"
	>
		<track kind="captions" />
	</video>
{:else}
	<img
		crossorigin="anonymous"
		src={finalSrc}
		class=" {className} object-cover rounded-full -translate-y-[1px]"
		alt="profile"
		draggable="false"
	/>
{/if}
