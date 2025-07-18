<script lang="ts">
	import TagInput from './Tags/TagInput.svelte';
	import TagList from './Tags/TagList.svelte';

	import type { Tag } from '$lib/types';
	import { getI18n } from '$lib/i18n/helpers';

	const dispatch = createEventDispatcher();
	const i18n = getI18n();

	export let tags: Tag[] = [];
</script>

<ul class="flex flex-row flex-wrap gap-1 line-clamp-1">
	<TagList
		{tags}
		on:delete={(e) => {
			dispatch('delete', e.detail);
		}}
	/>

	<TagInput
		label={tags.length == 0 ? $i18n.t('Add Tags') : ''}
		on:add={(e) => {
			dispatch('add', e.detail);
		}}
	/>
</ul>
