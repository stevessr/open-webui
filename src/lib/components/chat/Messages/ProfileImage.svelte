<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';
	import ProfileImage from '$lib/components/common/ProfileImage.svelte';

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/favicon.png`;

	$: processedSrc =
		src === ''
			? `${WEBUI_BASE_URL}/static/favicon.png`
			: src.startsWith(WEBUI_BASE_URL) ||
				  src.startsWith('https://www.gravatar.com/avatar/') ||
				  src.startsWith('data:') ||
				  src.startsWith('/')
				? src
				: `${WEBUI_BASE_URL}/user.gif`;
</script>

<ProfileImage src={processedSrc} class="{className} object-cover rounded-full" alt="profile" />
