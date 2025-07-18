<script>

	import Users from '$lib/components/admin/Users.svelte';

	onMount(() => {
		goto('/admin/users/overview');
	});
</script>

<Users />
