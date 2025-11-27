<script>
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import { config, functions, models, settings } from '$lib/stores';
	import { createNewFunction, getFunctions } from '$lib/apis/functions';
	import FunctionEditor from '$lib/components/admin/Functions/FunctionEditor.svelte';
	import { getModels } from '$lib/apis';
	import { compareVersion, extractFrontmatter } from '$lib/utils';
	import { WEBUI_VERSION } from '$lib/constants';

	const i18n = getContext('i18n');

	let mounted = false;
	let clone = false;
	let func = null;

	const saveHandler = async (data) => {
		console.log('🔍 [saveHandler] 开始执行');
		console.log('📊 [saveHandler] 接收到的数据：', data);
		console.log('📝 [saveHandler] data.content:', data.content);

		const manifest = extractFrontmatter(data.content);
		console.log('📋 [saveHandler] 提取的 manifest:', manifest);
		console.log('🔍 [saveHandler] manifest?.required_open_webui_version:', manifest?.required_open_webui_version);
		console.log('🌐 [saveHandler] WEBUI_VERSION:', WEBUI_VERSION);

		try {
			const comparisonResult = compareVersion(
				manifest?.required_open_webui_version ?? '0.0.0',
				WEBUI_VERSION
			);
			console.log('⚖️ [saveHandler] 版本比较结果：', comparisonResult);

			if (comparisonResult) {
				console.log('📉 [saveHandler] 版本过低，显示错误');
				toast.error(
					$i18n.t(
						'Neko version (v{{OPEN_WEBUI_VERSION}}) is lower than required version (v{{REQUIRED_VERSION}})',
						{
							OPEN_WEBUI_VERSION: WEBUI_VERSION,
							REQUIRED_VERSION: manifest?.required_open_webui_version ?? '0.0.0'
						}
					)
				);
				return;
			}
		} catch (error) {
			console.error('❌ [saveHandler] 版本比较出错：', error);
			console.error('❌ [saveHandler] 错误堆栈：', error.stack);
			toast.error('Version comparison failed');
			return;
		}

		console.log('✅ [saveHandler] 版本检查通过，继续保存');

		const res = await createNewFunction(localStorage.token, {
			id: data.id,
			name: data.name,
			meta: data.meta,
			content: data.content
		}).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			toast.success($i18n.t('Function created successfully'));
			functions.set(await getFunctions(localStorage.token));
			models.set(
				await getModels(
					localStorage.token,
					$config?.features?.enable_direct_connections && ($settings?.directConnections ?? null),
					false,
					true
				)
			);

			await goto('/admin/functions');
		}
	};

	onMount(() => {
		console.log('🚀 [Create Function Page] 页面加载完成');
		console.log('📊 [Create Function Page] 初始 func 数据：', func);
		console.log('🔍 [Create Function Page] clone 状态：', clone);

		window.addEventListener('message', async (event) => {
			if (
				!['https://openwebui.com', 'https://www.openwebui.com', 'http://localhost:9999'].includes(
					event.origin
				)
			)
				return;

			func = JSON.parse(event.data);
			console.log('📨 [Create Function Page] 从消息接收 func:', func);
		});

		if (window.opener ?? false) {
			window.opener.postMessage('loaded', '*');
		}

		if (sessionStorage.function) {
			func = JSON.parse(sessionStorage.function);
			sessionStorage.removeItem('function');

			console.log('💾 [Create Function Page] 从 sessionStorage 恢复 func:', func);
			clone = true;
		}

		mounted = true;
		console.log('✅ [Create Function Page] 页面挂载完成');
	});
</script>

{#if mounted}
	{#key func?.content}
		<div class="px-[16px] h-full">
			<FunctionEditor
				id={func?.id ?? ''}
				name={func?.name ?? ''}
				meta={func?.meta ?? { description: '' }}
				content={func?.content ?? ''}
				{clone}
				onSave={(value) => {
					saveHandler(value);
				}}
			/>
		</div>
	{/key}
{/if}
