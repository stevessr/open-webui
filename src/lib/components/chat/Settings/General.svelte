<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { getLanguages, changeLanguage } from '$lib/i18n';
	const dispatch = createEventDispatcher();

	import { models, settings, theme, user } from '$lib/stores';

	interface I18nContext {
		language: string;
		t: (key: string, options?: any) => string;
	}
	const _i18nContext = getContext<I18nContext | undefined>('i18n'); // Allow undefined
	
	const i18n = {
	  t: (key: string, options?: any): string => {
	    if (_i18nContext && typeof _i18nContext.t === 'function') {
	      return _i18nContext.t(key, options);
	    }
	    // console.warn(`[General.svelte] i18n.t is not available for key: "${key}". Falling back to key.`);
	    if (options && typeof options === 'object' && options !== null) {
	      let str = key;
	      for (const k in options) {
	        if (k !== 'defaultValue') { // Avoid processing a potential defaultValue option as a placeholder
	          const placeholder = new RegExp(`{{${k}}}`, 'g'); // Common placeholder format
	          str = str.replace(placeholder, options[k]);
	        }
	      }
	      return str;
	    }
	    return key;
	  },
	  get language(): string {
	    return _i18nContext && _i18nContext.language ? _i18nContext.language : 'en'; // Default language
	  }
	};

	import AdvancedParams from './Advanced/AdvancedParams.svelte';
	import Textarea from '$lib/components/common/Textarea.svelte';

	export let saveSettings: Function;
	export let getModels: Function;

	// General
	let themes = ['dark', 'light', 'rose-pine dark', 'rose-pine-dawn light', 'oled-dark'];
	let selectedTheme = 'system';

	let languages: Awaited<ReturnType<typeof getLanguages>> = [];
	let lang = i18n.language;
	let notificationEnabled = false;
	let system = '';
	let webuiBaseUrl: string = '';

	let showAdvanced = false;

	const toggleNotification = async () => {
		const permission = await Notification.requestPermission();

		if (permission === 'granted') {
			notificationEnabled = !notificationEnabled;
			saveSettings({ notificationEnabled: notificationEnabled });
		} else {
			toast.error(
				i18n.t(
					'Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.'
				)
			);
		}
	};

	// Advanced
	let requestFormat: string | null | object = null;
	let _requestFormatTextareaValue: string = ''; // Renamed for clarity
	let keepAlive: string | null = null;

	// Reactive update for _requestFormatTextareaValue (requestFormat -> display)
	$: {
		if (requestFormat === null) {
			_requestFormatTextareaValue = '';
		} else if (typeof requestFormat === 'object') {
			_requestFormatTextareaValue = JSON.stringify(requestFormat, null, 2);
		} else { // requestFormat is 'json' or a user-typed schema string
			_requestFormatTextareaValue = requestFormat;
		}
	}

	// Removed the cyclical reactive block that updated requestFormat from displayValue.
	// Input will be handled by an event handler on the textarea.

	let params = {
		// Advanced
		stream_response: null,
		function_calling: null,
		seed: null,
		temperature: null,
		reasoning_effort: null,
		logit_bias: null,
		frequency_penalty: null,
		presence_penalty: null,
		repeat_penalty: null,
		repeat_last_n: null,
		mirostat: null,
		mirostat_eta: null,
		mirostat_tau: null,
		top_k: null,
		top_p: null,
		min_p: null,
		stop: null,
		tfs_z: null,
		num_ctx: null,
		num_batch: null,
		num_keep: null,
		max_tokens: null,
		num_gpu: null,
		use_mmap: null,
		use_mlock: null,
		num_thread: null,
		template: null,
	};

	const validateJSON = (json: string) => {
		try {
			const obj = JSON.parse(json);

			if (obj && typeof obj === 'object') {
				return true;
			}
		} catch (e) {}
		return false;
	};

	const toggleRequestFormat = async () => {
		if (requestFormat === null) {
			requestFormat = 'json';
		} else {
			requestFormat = null;
		}

		saveSettings({ requestFormat: requestFormat !== null ? requestFormat : undefined });
	};

	const handleRequestFormatInput = (event: Event) => {
		const target = event.target as HTMLTextAreaElement;
		const newValue = target.value;

		// Update the logical requestFormat based on textarea input
		// _requestFormatTextareaValue will be updated reactively by the block above
		if (newValue === '') {
			requestFormat = null;
		} else {
			// Store as string; saveHandler will parse if it's a schema and not 'json'
			requestFormat = newValue;
		}
	};

	const saveHandler = async () => {
		if (typeof requestFormat === 'string' && requestFormat !== 'json') {
			if (validateJSON(requestFormat) === false) {
				toast.error(i18n.t('Invalid JSON schema'));
				return;
			} else {
				requestFormat = JSON.parse(requestFormat);
			}
		}

		saveSettings({
			system: system !== '' ? system : undefined,
			WEBUI_BASE_URL: webuiBaseUrl !== '' ? webuiBaseUrl : undefined,
			params: {
				stream_response: params.stream_response !== null ? params.stream_response : undefined,
				function_calling: params.function_calling !== null ? params.function_calling : undefined,
				seed: (params.seed !== null ? params.seed : undefined) ?? undefined,
				stop: undefined, // Since params.stop is always null, this branch is effectively dead.
				temperature: params.temperature !== null ? params.temperature : undefined,
				reasoning_effort: params.reasoning_effort !== null ? params.reasoning_effort : undefined,
				logit_bias: params.logit_bias !== null ? params.logit_bias : undefined,
				frequency_penalty: params.frequency_penalty !== null ? params.frequency_penalty : undefined,
				presence_penalty: params.frequency_penalty !== null ? params.frequency_penalty : undefined,
				repeat_penalty: params.frequency_penalty !== null ? params.frequency_penalty : undefined,
				repeat_last_n: params.repeat_last_n !== null ? params.repeat_last_n : undefined,
				mirostat: params.mirostat !== null ? params.mirostat : undefined,
				mirostat_eta: params.mirostat_eta !== null ? params.mirostat_eta : undefined,
				mirostat_tau: params.mirostat_tau !== null ? params.mirostat_tau : undefined,
				top_k: params.top_k !== null ? params.top_k : undefined,
				top_p: params.top_p !== null ? params.top_p : undefined,
				min_p: params.min_p !== null ? params.min_p : undefined,
				tfs_z: params.tfs_z !== null ? params.tfs_z : undefined,
				num_ctx: params.num_ctx !== null ? params.num_ctx : undefined,
				num_batch: params.num_batch !== null ? params.num_batch : undefined,
				num_keep: params.num_keep !== null ? params.num_keep : undefined,
				max_tokens: params.max_tokens !== null ? params.max_tokens : undefined,
				use_mmap: params.use_mmap !== null ? params.use_mmap : undefined,
				use_mlock: params.use_mlock !== null ? params.use_mlock : undefined,
				num_thread: params.num_thread !== null ? params.num_thread : undefined,
				num_gpu: params.num_gpu !== null ? params.num_gpu : undefined
			},
			keepAlive: keepAlive || undefined,
			requestFormat: requestFormat !== null ? requestFormat : undefined
		});
		dispatch('save');

		// Removed stringification of requestFormat here.
		// The reactive block $: { ... } will update requestFormatDisplayValue based on the new requestFormat state.
	};

	onMount(async () => {
		selectedTheme = localStorage.theme ?? 'system';

		languages = await getLanguages();

		notificationEnabled = $settings.notificationEnabled ?? false;
		system = $settings.system ?? '';
		webuiBaseUrl = ($settings as any).WEBUI_BASE_URL ?? '';

		requestFormat = ($settings as any).requestFormat ?? null;
		// Removed stringification of requestFormat here.
		// The reactive block $: { ... } will set requestFormatDisplayValue correctly.

		keepAlive = ($settings as any).keepAlive ?? null;

		const incomingParams = ($settings as any).params ?? {};
		params = { ...params, ...incomingParams };

		// Ensure params.stop and params.template remain null if AdvancedParams expects null
		params.stop = null; // Force to null to match AdvancedParams expectation
		params.template = null; // Keep template as null to match AdvancedParams if it still expects that
		// params.template = incomingParams?.template ?? null;
	});

	const applyTheme = (_theme: string) => {
		let themeToApply = _theme === 'oled-dark' ? 'dark' : _theme;

		if (_theme === 'system') {
			themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		}

		if (themeToApply === 'dark' && !_theme.includes('oled')) {
			document.documentElement.style.setProperty('--color-gray-800', '#333');
			document.documentElement.style.setProperty('--color-gray-850', '#262626');
			document.documentElement.style.setProperty('--color-gray-900', '#171717');
			document.documentElement.style.setProperty('--color-gray-950', '#0d0d0d');
		}

		themes
			.filter((e) => e !== themeToApply)
			.forEach((e) => {
				e.split(' ').forEach((e) => {
					document.documentElement.classList.remove(e);
				});
			});

		themeToApply.split(' ').forEach((e) => {
			document.documentElement.classList.add(e);
		});

		const metaThemeColor = document.querySelector('meta[name="theme-color"]');
		if (metaThemeColor) {
			if (_theme.includes('system')) {
				const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
					? 'dark'
					: 'light';
				console.log('Setting system meta theme color: ' + systemTheme);
				metaThemeColor.setAttribute('content', systemTheme === 'light' ? '#ffffff' : '#171717');
			} else {
				console.log('Setting meta theme color: ' + _theme);
				metaThemeColor.setAttribute(
					'content',
					_theme === 'dark'
						? '#171717'
						: _theme === 'oled-dark'
							? '#000000'
							: _theme === 'her'
								? '#983724'
								: '#ffffff'
				);
			}
		}

		if (typeof window !== 'undefined' && window.applyTheme) {
			window.applyTheme();
		}

		if (_theme.includes('oled')) {
			document.documentElement.style.setProperty('--color-gray-800', '#101010');
			document.documentElement.style.setProperty('--color-gray-850', '#050505');
			document.documentElement.style.setProperty('--color-gray-900', '#000000');
			document.documentElement.style.setProperty('--color-gray-950', '#000000');
			document.documentElement.classList.add('dark');
		}

		console.log(_theme);
	};

	const themeChangeHandler = (_theme: string) => {
		theme.set(_theme);
		localStorage.setItem('theme', _theme);
		applyTheme(_theme);
	};
</script>

<div class="flex flex-col h-full justify-between text-sm">
	<div class="  overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div class="">
			<div class=" mb-1 text-sm font-medium">{i18n.t('WebUI Settings')}</div>

			<div class="flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{i18n.t('Theme')}</div>
				<div class="flex items-center relative">
					<select
						class=" dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent outline-hidden text-right"
						bind:value={selectedTheme}
						placeholder="Select a theme"
						on:change={() => themeChangeHandler(selectedTheme)}
					>
						<option value="system">⚙️ {i18n.t('System')}</option>
						<option value="dark">🌑 {i18n.t('Dark')}</option>
						<option value="oled-dark">🌃 {i18n.t('OLED Dark')}</option>
						<option value="light">☀️ {i18n.t('Light')}</option>
						<option value="her">🌷 Her</option>
						<!-- <option value="rose-pine dark">🪻 {$i18n.t('Rosé Pine')}</option>
						<option value="rose-pine-dawn light">🌷 {$i18n.t('Rosé Pine Dawn')}</option> -->
					</select>
				</div>
			</div>

			<div class=" flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{i18n.t('Language')}</div>
				<div class="flex items-center relative">
					<select
						class=" dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent outline-hidden text-right"
						bind:value={lang}
						placeholder="Select a language"
						on:change={(e) => {
							changeLanguage(lang);
						}}
					>
						{#each languages as language}
							<option value={language['code']}>{language['title']}</option>
						{/each}
					</select>
				</div>
			</div>
			{#if i18n.language === 'en-US'}
				<div class="mb-2 text-xs text-gray-400 dark:text-gray-500">
					Couldn't find your language?
					<a
						class=" text-gray-300 font-medium underline"
						href="https://github.com/open-webui/open-webui/blob/main/docs/CONTRIBUTING.md#-translations-and-internationalization"
						target="_blank"
					>
						Help us translate Open WebUI!
					</a>
				</div>
			{/if}

			<div>
				<div class=" py-0.5 flex w-full justify-between">
					<div class=" self-center text-xs font-medium">{i18n.t('Notifications')}</div>

					<button
						class="p-1 px-3 text-xs flex rounded-sm transition"
						on:click={() => {
							toggleNotification();
						}}
						type="button"
					>
						{#if notificationEnabled === true}
							<span class="ml-2 self-center">{i18n.t('On')}</span>
						{:else}
							<span class="ml-2 self-center">{i18n.t('Off')}</span>
						{/if}
					</button>
				</div>
			</div>

			<div class="flex w-full flex-col py-1">
				<div class="self-center text-xs font-medium">{i18n.t('Custom WEBUI Base URL')}</div>
				<input
					type="text"
					class="w-full text-sm dark:text-gray-300 dark:bg-gray-900 outline-hidden p-2 rounded-sm bg-gray-100 mt-1"
					placeholder={i18n.t('e.g., http://localhost:3000')}
					bind:value={webuiBaseUrl}
				/>
				<div class="mt-1 text-xs text-gray-400 dark:text-gray-500">
					{i18n.t('Overrides the default base URL for the WebUI. Requires restart to take full effect.')}
				</div>
			</div>
		</div>

		{#if $user?.role === 'admin'}
			<hr class="border-gray-50 dark:border-gray-850 my-3" />

			<div>
				<div class=" my-2.5 text-sm font-medium">{i18n.t('System Prompt')}</div>
				<Textarea
					bind:value={system}
					className="w-full text-sm bg-white dark:text-gray-300 dark:bg-gray-900 outline-hidden resize-none"
					rows={4}
					placeholder={i18n.t('Enter system prompt here')}
				/>
			</div>

			<div class="mt-2 space-y-3 pr-1.5">
				<div class="flex justify-between items-center text-sm">
					<div class="  font-medium">{i18n.t('Advanced Parameters')}</div>
					<button
						class=" text-xs font-medium text-gray-500"
						type="button"
						on:click={() => {
							showAdvanced = !showAdvanced;
						}}>{showAdvanced ? i18n.t('Hide') : i18n.t('Show')}</button
					>
				</div>

				{#if showAdvanced}
					<AdvancedParams admin={$user?.role === 'admin'} bind:params={params} />
					<hr class=" border-gray-100 dark:border-gray-850" />

					<div class=" w-full justify-between">
						<div class="flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{i18n.t('Keep Alive')}</div>

							<button
								class="p-1 px-3 text-xs flex rounded-sm transition"
								type="button"
								on:click={() => {
									keepAlive = keepAlive === null ? '5m' : null;
								}}
							>
								{#if keepAlive === null}
									<span class="ml-2 self-center"> {i18n.t('Default')} </span>
								{:else}
									<span class="ml-2 self-center"> {i18n.t('Custom')} </span>
								{/if}
							</button>
						</div>

						{#if keepAlive !== null}
							<div class="flex mt-1 space-x-2">
								<input
									class="w-full text-sm dark:text-gray-300 dark:bg-gray-850 outline-hidden"
									type="text"
									placeholder={i18n.t("e.g. '30s','10m'. Valid time units are 's', 'm', 'h'.")}
									bind:value={keepAlive}
								/>
							</div>
						{/if}
					</div>

					<div>
						<div class=" flex w-full justify-between">
							<div class=" self-center text-xs font-medium">{i18n.t('Request Mode')}</div>

							<button
								class="p-1 px-3 text-xs flex rounded-sm transition"
								on:click={() => {
									toggleRequestFormat();
								}}
							>
								{#if requestFormat === null}
									<span class="ml-2 self-center"> {i18n.t('Default')} </span>
								{:else}
									<!-- <svg
		                          xmlns="http://www.w3.org/2000/svg"
		                          viewBox="0 0 20 20"
		                          fill="currentColor"
		                          class="w-4 h-4 self-center"
		                      >
		                          <path
		                              d="M10 2a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 2zM10 15a.75.75 0 01.75.75v1.5a.75.75 0 01-1.5 0v-1.5A.75.75 0 0110 15zM10 7a3 3 0 100 6 3 3 0 000-6zM15.657 5.404a.75.75 0 10-1.06-1.06l-1.061 1.06a.75.75 0 001.06 1.06l1.06-1.06zM6.464 14.596a.75.75 0 10-1.06-1.06l-1.06 1.06a.75.75 0 001.06 1.06l1.06-1.06zM18 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 0118 10zM5 10a.75.75 0 01-.75.75h-1.5a.75.75 0 010-1.5h1.5A.75.75 0 015 10zM14.596 15.657a.75.75 0 001.06-1.06l-1.06-1.061a.75.75 0 10-1.06 1.06l1.06 1.06zM5.404 6.464a.75.75 0 001.06-1.06l-1.06-1.06a.75.75 0 10-1.061 1.06l1.06 1.06z"
		                          />
		                      </svg> -->
									<span class="ml-2 self-center"> {i18n.t('JSON')} </span>
								{/if}
							</button>
						</div>

						{#if requestFormat !== null}
							<div class="flex mt-1 space-x-2">
								<Textarea
									className="w-full  text-sm dark:text-gray-300 dark:bg-gray-900 outline-hidden"
									placeholder={i18n.t('e.g. "json" or a JSON schema')}
									value={_requestFormatTextareaValue}
									on:input={handleRequestFormatInput}
								/>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<div class="flex justify-end pt-3 text-sm font-medium">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
			on:click={() => {
				saveHandler();
			}}
		>
			{i18n.t('Save')}
		</button>
	</div>
</div>
