<script lang="ts">
	import { createEventDispatcher, getContext } from 'svelte';
	import { tags } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import DataList from '$lib/components/common/DataList.svelte';
	import { filterTagSuggestions } from '$lib/constants/vendorTags';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	export let label = '';
	export let suggestionTags = [];
	export let modelInfo = {};

	let showTagInput = false;
	let tagName = '';

	// 使用厂商标签系统生成选项
	$: tagOptions = [
		// 如果用户输入了内容，优先显示匹配的推荐标签
		...filterTagSuggestions(tagName.trim(), modelInfo)
	];

	const addTagHandler = async () => {
		tagName = tagName.trim();
		if (tagName !== '') {
			dispatch('add', tagName);
			tagName = '';
			showTagInput = false;
		} else {
			toast.error($i18n.t(`Invalid Tag`));
		}
	};

	const handleTagSelect = (selectedTag: string) => {
		// 如果是新建标签，去除"(新建)"后缀
		const cleanTag = selectedTag.replace(' (新建)', '');
		tagName = cleanTag;
		// 选择后立即添加
		addTagHandler();
	};

	// 处理键盘事件
	const handleKeydown = (event) => {
		if (event.key === 'Enter') {
			event.preventDefault();
			addTagHandler();
		} else if (event.key === 'Escape') {
			tagName = '';
			showTagInput = false;
		} else if (event.key === 'Tab') {
			// Tab 键自动补全第一个匹配项
			event.preventDefault();
			if (tagOptions.length > 0) {
				const firstOption = tagOptions[0].value.replace(' (新建)', '');
				tagName = firstOption;
			}
		}
	};

	// 失去焦点时自动隐藏输入框
	const handleBlur = () => {
		setTimeout(() => {
			if (tagName.trim() === '') {
				showTagInput = false;
			}
		}, 200);
	};

	// 输入时自动显示下拉列表
	const handleInputChange = () => {
		if (tagName.trim() && !showTagInput) {
			showTagInput = true;
		}
	};
</script>

<div class="px-0.5 flex {showTagInput ? 'flex-row-reverse' : ''}">
	{#if showTagInput}
		<div class="flex items-center gap-2">
			<DataList
				bind:value={tagName}
				options={tagOptions}
				placeholder={$i18n.t('Add a tag')}
				ariaLabel={$i18n.t('Add a tag')}
				onSelect={handleTagSelect}
				onKeydown={handleKeydown}
				on:blur={handleBlur}
				className="transv2 px-2 py-1 cursor-pointer self-center text-xs h-fit bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-md outline-hidden line-clamp-1 w-[12rem] focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
			/>
			{#if suggestionTags.length > 0}
				<datalist id="tagOptions">
					{#each suggestionTags as tag}
						<option value={tag.name} />
					{/each}
				</datalist>
			{/if}

			<button
				type="button"
				aria-label={$i18n.t('Save Tag')}
				on:click={addTagHandler}
				class="p-1 rounded-full bg-blue-500 hover:bg-blue-600 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				disabled={!tagName.trim()}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 16 16"
					fill="currentColor"
					stroke-width="2"
					aria-hidden="true"
					class="w-3 h-3"
				>
					<path
						fill-rule="evenodd"
						d="M12.416 3.376a.75.75 0 0 1 .208 1.04l-5 7.5a.75.75 0 0 1-1.154.114l-3-3a.75.75 0 0 1 1.06-1.06l2.353 2.353 4.493-6.74a.75.75 0 0 1 1.04-.207Z"
						clip-rule="evenodd"
					/>
				</svg>
			</button>

			<button
				type="button"
				aria-label={$i18n.t('Cancel')}
				on:click={() => {
					tagName = '';
					showTagInput = false;
				}}
				class="p-1 rounded-full bg-gray-300 hover:bg-gray-400 dark:bg-gray-600 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 transition-colors"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 16 16"
					fill="currentColor"
					aria-hidden="true"
					class="w-3 h-3"
				>
					<path
						d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8 2.146 2.854Z"
					/>
				</svg>
			</button>
		</div>
	{/if}

	<button
		class="cursor-pointer self-center p-0.5 flex h-fit items-center rounded-full transition border border-blue-300 dark:border-blue-600 border-dashed hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
		type="button"
		aria-label={$i18n.t('Add Tag')}
		on:click={() => {
			showTagInput = !showTagInput;
			if (showTagInput) {
				// 延迟聚焦，确保 DOM 已更新
				setTimeout(() => {
					const input = document.querySelector('[aria-label="Add a tag"]');
					if (input) input.focus();
				}, 0);
			}
		}}
	>
		<div class="m-auto self-center">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 16 16"
				aria-hidden="true"
				fill="currentColor"
				class="size-2.5 text-blue-500 dark:text-blue-400 {showTagInput ? 'rotate-45' : ''} transition-all transform"
			>
				<path
					d="M8.75 3.75a.75.75 0 0 0-1.5 0v3.5h-3.5a.75.75 0 0 0 0 1.5h3.5v3.5a.75.75 0 0 0 1.5 0v-3.5h3.5a.75.75 0 0 0 0-1.5h-3.5v-3.5Z"
				/>
			</svg>
		</div>
	</button>

	{#if label && !showTagInput}
		<span class="text-xs pl-2 self-center text-gray-500 dark:text-gray-400">{label}</span>
	{/if}
</div>
