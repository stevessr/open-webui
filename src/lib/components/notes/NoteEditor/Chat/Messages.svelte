<script lang="ts">

	import Message from './Message.svelte';
	import { getI18n } from '$lib/i18n/helpers';

	const i18n = getI18n();

	export let messages = [];
	export let onInsert = (content: string) => {};
</script>

<div class="space-y-3 pb-12">
	{#each messages as message, idx}
		<Message
			{message}
			{idx}
			onInsert={() => {
				onInsert(message?.content ?? '');
			}}
			onEdit={() => {
				messages = messages.map((msg, messageIdx) => {
					if (messageIdx === idx) {
						return { ...msg, edit: true };
					}
					return msg;
				});
			}}
			onDelete={() => {
				messages = messages.filter((message, messageIdx) => messageIdx !== idx);
			}}
		/>
	{/each}
</div>
