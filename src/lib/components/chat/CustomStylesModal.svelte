<script lang="ts">

	import Modal from '../common/Modal.svelte';
	import CodeEditor from '../common/CodeEditor.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import XMark from '$lib/components/icons/XMark.svelte';
	import Code from '$lib/components/icons/Code.svelte';
	import { getI18n } from '$lib/i18n/helpers';

	const i18n = getI18n();

	export let show = false;

	let customCSS = '';
	let customJS = '';

	// Load custom styles from localStorage when modal opens
	$: if (show) {
		loadCustomStyles();
	}

	const loadCustomStyles = () => {
		customCSS = localStorage.getItem('customCSS') || '';
		customJS = localStorage.getItem('customJS') || '';
	};

	const saveCustomStyles = () => {
		try {
			// Save to localStorage
			localStorage.setItem('customCSS', customCSS);
			localStorage.setItem('customJS', customJS);

			// Trigger custom styles update
			window.dispatchEvent(
				new CustomEvent('customStylesUpdated', {
					detail: { customCSS, customJS }
				})
			);

			toast.success($i18n.t('Custom styles saved successfully'));
			show = false;
		} catch (error) {
			console.error('Failed to save custom styles:', error);
			toast.error($i18n.t('Failed to save custom styles'));
		}
	};

	const resetCustomStyles = () => {
		customCSS = '';
		customJS = '';
	};

	const applyPreview = () => {
		// Trigger a temporary preview update
		window.dispatchEvent(
			new CustomEvent('customStylesUpdated', {
				detail: { customCSS, customJS }
			})
		);
		toast.success($i18n.t('Preview applied'));
	};
</script>

<Modal bind:show size="lg" draggable={false}>
	<div class="text-gray-700 dark:text-gray-100">
		<div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-2">
			<div class="flex items-center gap-2">
				<Code className="size-5" />
				<div class="text-lg font-medium self-center">{$i18n.t('Custom Styles')}</div>
			</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className="size-5" />
			</button>
		</div>

		<div class="flex flex-col w-full p-5 space-y-4 dark:text-gray-200">
			<div class="text-sm text-gray-600 dark:text-gray-400">
				{$i18n.t(
					'Customize the appearance and functionality of the interface with your own CSS and JavaScript code.'
				)}
			</div>

			<!-- Custom CSS Section -->
			<div class="space-y-2">
				<div class="flex items-center gap-2">
					<div class="text-sm font-medium">{$i18n.t('Custom CSS')}</div>
					<Tooltip
						content={$i18n.t('Add custom CSS styles to customize the appearance of the interface')}
					>
						<div class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-help">
							<svg class="size-4" fill="currentColor" viewBox="0 0 20 20">
								<path
									fill-rule="evenodd"
									d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</Tooltip>
				</div>
				<div
					class="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden"
					style="height: 200px;"
				>
					<CodeEditor
						id="custom-css-editor"
						lang="css"
						bind:value={customCSS}
						boilerplate="/* Enter your custom CSS here */"
					/>
				</div>
			</div>

			<!-- Custom JavaScript Section -->
			<div class="space-y-2">
				<div class="flex items-center gap-2">
					<div class="text-sm font-medium">{$i18n.t('Custom JavaScript')}</div>
					<Tooltip content={$i18n.t('Add custom JavaScript code to extend functionality')}>
						<div class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-help">
							<svg class="size-4" fill="currentColor" viewBox="0 0 20 20">
								<path
									fill-rule="evenodd"
									d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</Tooltip>
				</div>
				<div
					class="border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden"
					style="height: 200px;"
				>
					<CodeEditor
						id="custom-js-editor"
						lang="javascript"
						bind:value={customJS}
						boilerplate={`// Enter your custom JavaScript here
console.log("Custom script loaded");`}
					/>
				</div>
			</div>

			<!-- Action Buttons -->
			<div
				class="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700"
			>
				<div class="flex gap-2">
					<button
						class="px-4 py-2 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
						on:click={applyPreview}
					>
						{$i18n.t('Preview')}
					</button>
					<button
						class="px-4 py-2 text-sm bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
						on:click={resetCustomStyles}
					>
						{$i18n.t('Reset')}
					</button>
				</div>
				<div class="flex gap-2">
					<button
						class="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
						on:click={() => {
							show = false;
						}}
					>
						{$i18n.t('Cancel')}
					</button>
					<button
						class="px-4 py-2 text-sm bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
						on:click={saveCustomStyles}
					>
						{$i18n.t('Save')}
					</button>
				</div>
			</div>
		</div>

		<!-- Help Section -->
		<div class="px-5 pb-4">
			<details class="text-sm">
				<summary
					class="cursor-pointer text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
				>
					{$i18n.t('Examples and Tips')}
				</summary>
				<div class="mt-2 space-y-2 text-xs text-gray-500 dark:text-gray-400">
					<div>
						<strong>CSS Example:</strong>
						<code class="block mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded"> </code>
					</div>
					<div>
						<strong>JavaScript Example:</strong>
						<code class="block mt-1 p-2 bg-gray-100 dark:bg-gray-800 rounded"> </code>
					</div>
				</div>
			</details>
		</div>
	</div>
</Modal>
