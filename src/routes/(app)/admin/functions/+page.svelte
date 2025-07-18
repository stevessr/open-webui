<script>

	import Functions from '$lib/components/admin/Functions.svelte';

	onMount(async () => {
		await Promise.all([
			(async () => {
				functions.set(await getFunctions(localStorage.token));
			})()
		]);
	});
</script>

{#if $functions !== null}
	<Functions />
{/if}
