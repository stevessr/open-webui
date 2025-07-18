<script lang="ts">

	import type { i18n as i18nType } from 'i18next';

	const i18n: Writable<i18nType> = getContext('i18n');

	import PromptEditor from '$lib/components/workspace/Prompts/PromptEditor.svelte';

	import type { Prompt } from '$lib/stores';

	let prompt: Prompt | null = null;
	const onSubmit = async (_prompt: Prompt) => {
		console.log(_prompt);
		const prompt = await updatePromptByCommand(localStorage.token, _prompt).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (prompt) {
			toast.success($i18n.t('Prompt updated successfully'));
			await prompts.set(await getPrompts(localStorage.token));
			await goto('/workspace/prompts');
		}
	};

	onMount(async () => {
		const command = $page.url.searchParams.get('command');
		if (command) {
			const _prompt = await getPromptByCommand(
				localStorage.token,
				command.replace(/\//g, '')
			).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (_prompt) {
				prompt = {
					title: _prompt.title,
					command: _prompt.command,
					content: _prompt.content,
					access_control: _prompt?.access_control === undefined ? {} : _prompt?.access_control,
					user_id: _prompt.user_id,
					timestamp: _prompt.timestamp
				};
			} else {
				goto('/workspace/prompts');
			}
		} else {
			goto('/workspace/prompts');
		}
	});
</script>

{#if prompt}
	<PromptEditor {prompt} {onSubmit} edit />
{/if}
