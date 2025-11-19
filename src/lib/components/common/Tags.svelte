<script lang="ts">
	import TagInput from './Tags/TagInput.svelte';
	import TagList from './Tags/TagList.svelte';
	import { getContext, createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	export let tags = [];
	export let modelInfo: { owned_by?: string; name?: string; id?: string; base_model_id?: string } = {};
</script>

<ul class="flex flex-row flex-wrap gap-[0.3rem] line-clamp-1">
	<TagList
		{tags}
		on:delete={(e) => {
			dispatch('delete', e.detail);
		}}
	/>

	<TagInput
		label={tags.length == 0 ? $i18n.t('Add Tags') : ''}
		{modelInfo}
		on:add={(e) => {
			dispatch('add', e.detail);
		}}
	/>
</ul>
