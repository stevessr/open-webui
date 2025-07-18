<script lang="ts">

	import type { Prompt } from '$lib/stores';
	import type { ModelConfig } from '$lib/apis';

	import ModelEditor from '$lib/components/workspace/Models/ModelEditor.svelte';

	const i18n = getContext<any>('i18n');

	const onSubmit = async (modelInfo: ModelConfig) => {
		if ($models.find((m) => m.id === modelInfo.id)) {
			toast.error(
				`Error: A model with the ID '${modelInfo.id}' already exists. Please select a different ID to proceed.`
			);
			return;
		}

		if (modelInfo.id === '') {
			toast.error('Error: Model ID cannot be empty. Please enter a valid ID to proceed.');
			return;
		}

		if (modelInfo) {
			const res = await createNewModel(localStorage.token, {
				...modelInfo,
				meta: {
					...modelInfo.meta,
					profile_image_url:
						modelInfo.meta.profile_image_url ?? `${WEBUI_BASE_URL}/static/favicon.png`,
					suggestion_prompts: modelInfo.meta.suggestion_prompts
						? modelInfo.meta.suggestion_prompts.filter((prompt: Prompt) => prompt.content !== '')
						: null
				},
				params: { ...modelInfo.params }
			}).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				await models.set(
					await getModels(
						localStorage.token,
						($config?.features?.enable_direct_connections &&
							($settings?.directConnections ?? null)) as object | null | undefined
					)
				);
				toast.success(i18n.t('Model created successfully!'));
				await goto('/workspace/models');
			}
		}
	};

	let model: ModelConfig | null = null;

	onMount(async () => {
		window.addEventListener('message', async (event: MessageEvent) => {
			if (
				!['https://openwebui.com', 'https://www.openwebui.com', 'http://localhost:5173'].includes(
					event.origin
				)
			) {
				return;
			}

			let data = JSON.parse(event.data);

			if (data?.info) {
				data = data.info;
			}

			model = data;
		});

		if (window.opener ?? false) {
			window.opener.postMessage('loaded', '*');
		}

		if (sessionStorage.model) {
			model = JSON.parse(sessionStorage.model);
			sessionStorage.removeItem('model');
		}
	});
</script>

{#key model?.id}
	<ModelEditor {model} {onSubmit} />
{/key}
