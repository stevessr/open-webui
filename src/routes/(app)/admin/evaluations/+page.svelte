<script>

	import Evaluations from '$lib/components/admin/Evaluations.svelte';

	onMount(() => {
		goto('/admin/evaluations/leaderboard');
	});
</script>

<Evaluations />
