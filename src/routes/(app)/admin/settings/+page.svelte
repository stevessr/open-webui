<script>

	import Settings from '$lib/components/admin/Settings.svelte';

	onMount(() => {
		goto('/admin/settings/general');
	});
</script>

<Settings />
