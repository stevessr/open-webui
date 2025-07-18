<script>

	const dispatch = createEventDispatcher();

	export let nodes;
	export let nodeTypes;
	export let edges;
</script>

<SvelteFlow
	{nodes}
	{nodeTypes}
	{edges}
	fitView
	minZoom={0.001}
	colorMode={$theme.includes('dark')
		? 'dark'
		: $theme === 'system'
			? window.matchMedia('(prefers-color-scheme: dark)').matches
				? 'dark'
				: 'light'
			: 'light'}
	nodesConnectable={false}
	nodesDraggable={false}
	on:nodeclick={(e) => dispatch('nodeclick', e.detail)}
	oninit={() => {
		console.log('Flow initialized');
	}}
>
	<Controls showLock={false} />
	<Background variant={BackgroundVariant.Dots} />
</SvelteFlow>
