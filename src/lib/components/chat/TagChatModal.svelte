<script lang="ts">

	import Modal from '../common/Modal.svelte';

	import Tags from '../common/Tags.svelte';
	import { getI18n } from '$lib/i18n/helpers';

	const i18n = getI18n();

	export let tags;
	export let deleteTag: Function;
	export let addTag: Function;

	export let show = false;
</script>

<Modal bind:show size="xs" draggable={false}>
	<div class="px-4 pt-4 pb-5 w-full flex flex-col justify-center">
		<Tags
			{tags}
			on:delete={(e) => {
				deleteTag(e.detail);
			}}
			on:add={(e) => {
				addTag(e.detail);
			}}
		/>
	</div>
</Modal>
