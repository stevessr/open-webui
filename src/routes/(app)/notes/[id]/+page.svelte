<script lang="ts">
	import { page } from '$app/stores';
	import { showSidebar } from '$lib/stores';
	import Background from '$lib/components/Background.svelte';

	import NoteEditor from '$lib/components/notes/NoteEditor.svelte';
</script>

<div id="note-container" class="w-full h-full {$showSidebar ? 'md:max-w-[calc(100%-260px)]' : ''}">
	<Background opacity={0.3} />
	<NoteEditor id={$page.params.id} />
</div>
