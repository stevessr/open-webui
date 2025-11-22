<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount } from 'svelte';

	const dispatch = createEventDispatcher();

	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let url: string = '';
	export let key: string = '';
	export let config: any = {};

	export let idx: number = 0;
	export let deleteHandler: Function;

	let deleteConfirm = false;

	const deleteConnectionHandler = () => {
		deleteHandler(idx);
	};

	let showAdvanced = false;

	// Ensure config has default structure
	if (!config) config = {};
	if (!config.enable) config.enable = true;
	if (!config.model_ids) config.model_ids = [];

	// Helper functions to get/set values
	const getEnable = () => config?.enable ?? true;
	const setEnable = (val: boolean) => {
		config = { ...config, enable: val };
	};

	const getModelIds = () => (config?.model_ids ?? []).join('\n');
	const setModelIds = (val: string) => {
		config = {
			...config,
			model_ids: val ? val.split('\n').filter((id) => id.trim() !== '') : []
		};
	};
</script>

<div class="flex flex-col gap-2 py-3">
	<div class="flex w-full gap-2">
		<div class="flex-1">
			<div class="mb-1.5 text-xs font-medium">API Base URL</div>

			<div class="flex-1">
				<input
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
					placeholder="https://api.anthropic.com"
					bind:value={url}
					autocomplete="off"
				/>
			</div>
		</div>

		<div class="flex-1">
			<div class="mb-1.5 text-xs font-medium">API Key</div>

			<div class="flex-1">
				<input
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none"
					placeholder="Enter API Key"
					bind:value={key}
					autocomplete="off"
					type="password"
				/>
			</div>
		</div>

		{#if idx !== 0}
			<div class="mt-6">
				{#if deleteConfirm}
					<div class="flex gap-1">
						<button
							class=" px-2 py-2 rounded-lg text-xs font-medium bg-red-500 hover:bg-red-600 text-white transition"
							on:click={() => {
								deleteConnectionHandler();
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z"
								/>
							</svg>
						</button>

						<button
							class=" px-2 py-2 rounded-lg text-xs font-medium bg-gray-100 hover:bg-gray-200 text-gray-800 transition"
							on:click={() => {
								deleteConfirm = false;
							}}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 16 16"
								fill="currentColor"
								class="w-3 h-3"
							>
								<path
									d="M5.28 4.22a.75.75 0 0 0-1.06 1.06L6.94 8l-2.72 2.72a.75.75 0 1 0 1.06 1.06L8 9.06l2.72 2.72a.75.75 0 1 0 1.06-1.06L9.06 8l2.72-2.72a.75.75 0 0 0-1.06-1.06L8 6.94 5.28 4.22Z"
								/>
							</svg>
						</button>
					</div>
				{:else}
					<button
						class=" px-2 py-2 rounded-lg text-xs font-medium bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition"
						on:click={() => {
							deleteConfirm = true;
						}}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 16 16"
							fill="currentColor"
							class="w-3 h-3"
						>
							<path
								fill-rule="evenodd"
								d="M5 3.25V4H2.75a.75.75 0 0 0 0 1.5h.3l.815 8.15A1.5 1.5 0 0 0 5.357 15h5.285a1.5 1.5 0 0 0 1.493-1.35l.815-8.15h.3a.75.75 0 0 0 0-1.5H11v-.75A2.25 2.25 0 0 0 8.75 1h-1.5A2.25 2.25 0 0 0 5 3.25Zm2.25-.75a.75.75 0 0 0-.75.75V4h3v-.75a.75.75 0 0 0-.75-.75h-1.5ZM6.05 6a.75.75 0 0 1 .787.713l.275 5.5a.75.75 0 0 1-1.498.075l-.275-5.5A.75.75 0 0 1 6.05 6Zm3.9 0a.75.75 0 0 1 .712.787l-.275 5.5a.75.75 0 0 1-1.498-.075l.275-5.5a.75.75 0 0 1 .786-.711Z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
				{/if}
			</div>
		{/if}
	</div>

	<div class="mb-1 text-xs font-medium">
		<button
			class="flex items-center gap-1"
			on:click={() => {
				showAdvanced = !showAdvanced;
			}}
		>
			Advanced
			<div class="ml-0.5 {showAdvanced ? 'rotate-180' : ''} transition-transform">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 16 16"
					fill="currentColor"
					class="w-3 h-3"
				>
					<path
						fill-rule="evenodd"
						d="M4.22 6.22a.75.75 0 0 1 1.06 0L8 8.94l2.72-2.72a.75.75 0 1 1 1.06 1.06l-3.25 3.25a.75.75 0 0 1-1.06 0L4.22 7.28a.75.75 0 0 1 0-1.06Z"
						clip-rule="evenodd"
					/>
				</svg>
			</div>
		</button>
	</div>

	{#if showAdvanced}
		<div class="flex flex-col gap-2">
			<div class="flex items-center justify-between gap-2">
				<div class="flex items-center gap-2">
					<div class="flex-1 text-xs font-medium">Enable</div>

					<div>
						<Tooltip content="Enable/Disable this connection">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-3 h-3"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z"
								/>
							</svg>
						</Tooltip>
					</div>
				</div>

				<div>
					<Switch
						state={getEnable()}
						on:change={(e) => {
							setEnable(e.detail);
						}}
					/>
				</div>
			</div>

			<div class="flex flex-col gap-1">
				<div class="flex items-center gap-2">
					<div class="flex-1 text-xs font-medium">Model IDs (optional)</div>

					<div>
						<Tooltip
							content="Specify which models to use from this connection. Leave empty to use all available models."
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
								stroke-width="1.5"
								stroke="currentColor"
								class="w-3 h-3"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z"
								/>
							</svg>
						</Tooltip>
					</div>
				</div>

				<textarea
					class="w-full rounded-lg py-2 px-4 text-sm bg-gray-50 dark:text-gray-300 dark:bg-gray-850 outline-none resize-none"
					placeholder={`claude-3-5-sonnet-20241022\nclaude-3-opus-20240229`}
					rows="3"
					value={getModelIds()}
					on:input={(e) => {
						setModelIds(e.currentTarget.value);
					}}
				/>

				<div class="text-xs text-gray-500">One model ID per line</div>
			</div>
		</div>
	{/if}

	<hr class="dark:border-gray-850" />
</div>
