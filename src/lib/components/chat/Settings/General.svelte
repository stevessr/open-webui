<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { get, type Readable } from 'svelte/store';
	import { slide, fade } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import type { i18n as i18nType } from 'i18next';

	// Custom transition that combines slide and fade
	function slideAndFade(node: Element, params: { delay?: number; duration?: number } = {}) {
		const slideTransition = slide(node, { duration: 300, easing: quintOut, ...params });
		const fadeTransition = fade(node, { duration: 200, delay: params.delay || 0 });

		return {
			duration: Math.max(slideTransition.duration || 300, fadeTransition.duration || 200),
			css: (t: number, u: number) => {
				const slideCSS = slideTransition.css ? slideTransition.css(t, u) : '';
				const fadeCSS = fadeTransition.css ? fadeTransition.css(t, u) : '';
				return `${slideCSS} ${fadeCSS}`;
			}
		};
	}
	import { getLanguages, changeLanguage } from '$lib/i18n';
	const dispatch = createEventDispatcher();

	import { models, settings, theme, user } from '$lib/stores';
	import {
		generateThemeFromBackground,
		applyMaterialTheme,
		removeMaterialTheme
	} from '$lib/utils/materialThemeGenerator';

	const i18n = getContext('i18n') as Readable<i18nType>;

	import AdvancedParams, {
		defaultParams
	} from '$lib/components/chat/Settings/Advanced/AdvancedParams.svelte';
	import Textarea from '$lib/components/common/Textarea.svelte';
	export let saveSettings: Function;
	export let getModels: Function;

	// General
	let themes = ['dark', 'light', 'oled-dark', 'material-design'];
	let selectedTheme = 'system';

	let languages: Awaited<ReturnType<typeof getLanguages>> = [];
	let lang = get(i18n).language;
	let notificationEnabled = false;
let showUserGravatar = false;
	let system = '';

	let showAdvanced = false;

	const toggleNotification = async () => {
		const permission = await Notification.requestPermission();

		if (permission === 'granted') {
			notificationEnabled = !notificationEnabled;
			saveSettings({ notificationEnabled: notificationEnabled });
		} else {
			toast.error(
				get(i18n).t(
					'Response notifications cannot be activated as the website permissions have been denied. Please visit your browser settings to grant the necessary access.'
				)
			);
		}
	};

	let advancedParams = JSON.parse(JSON.stringify(defaultParams));

	const saveHandler = async () => {
		const paramsToSave: Record<string, any> = {};
		for (const key in advancedParams) {
			if (advancedParams[key] !== null) {
				paramsToSave[key] = advancedParams[key];
			}
		}

		if (typeof paramsToSave['stop'] === 'string') {
			paramsToSave['stop'] = paramsToSave['stop'].split(',').filter((e) => e.trim() !== '');
		} else {
			delete paramsToSave['stop'];
		}

		await saveSettings({
			system: system !== '' ? system : undefined,
			params: paramsToSave
		});
		dispatch('save');
	};

	onMount(async () => {
		selectedTheme = localStorage.theme ?? 'system';

		languages = await getLanguages();

		notificationEnabled = $settings.notificationEnabled ?? false;
	showUserGravatar = $settings.showUserGravatar ?? false;
		system = $settings.system ?? '';

		advancedParams = { ...advancedParams, ...$settings.params };
		advancedParams.stop = $settings?.params?.stop ? ($settings?.params?.stop ?? []).join(',') : null;
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
								: _theme === 'material-design'
									? '#6200EE'
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

	const themeChangeHandler = async (_theme: string) => {
		theme.set(_theme);
		localStorage.setItem('theme', _theme);
		applyTheme(_theme);

		// Handle Material Design theme
		if (_theme === 'material-design') {
			const backgroundImageUrl = $settings?.backgroundImageUrl;
			if (backgroundImageUrl) {
				try {
					const palette = await generateThemeFromBackground(backgroundImageUrl);
					applyMaterialTheme(palette);
				} catch (error) {
					console.error('Failed to generate Material Design theme:', error);
					// Apply default Material Design theme
					applyMaterialTheme({
						primary: '#6200EE',
						primaryVariant: '#3700B3',
						secondary: '#03DAC6',
						secondaryVariant: '#018786',
						background: '#FFFFFF',
						surface: '#FFFFFF',
						error: '#B00020',
						onPrimary: '#FFFFFF',
						onSecondary: '#000000',
						onBackground: '#000000',
						onSurface: '#000000',
						onError: '#FFFFFF'
					});
				}
			} else {
				// Apply default Material Design theme when no background image
				applyMaterialTheme({
					primary: '#6200EE',
					primaryVariant: '#3700B3',
					secondary: '#03DAC6',
					secondaryVariant: '#018786',
					background: '#FFFFFF',
					surface: '#FFFFFF',
					error: '#B00020',
					onPrimary: '#FFFFFF',
					onSecondary: '#000000',
					onBackground: '#000000',
					onSurface: '#000000',
					onError: '#FFFFFF'
				});
			}
		} else {
			// Remove Material Design theme when switching to other themes
			removeMaterialTheme();
		}
	};
</script>

<div class="flex flex-col h-full justify-between text-sm" id="tab-general">
	<div class="  overflow-y-scroll max-h-[28rem] lg:max-h-full">
		<div class="">
			<div class=" mb-1 text-sm font-medium">{$i18n.t('WebUI Settings')}</div>

			<div class="flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Theme')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent text-right {$settings.highContrastMode
							? ''
							: 'outline-hidden'}"
						bind:value={selectedTheme}
						placeholder="Select a theme"
						on:change={() => themeChangeHandler(selectedTheme)}
					>
						<option value="system">⚙️ {$i18n.t('System')}</option>
						<option value="dark">🌑 {$i18n.t('Dark')}</option>
						<option value="oled-dark">🌃 {$i18n.t('OLED Dark')}</option>
						<option value="light">☀️ {$i18n.t('Light')}</option>
						<option value="her">🌷 Her</option>
						<option value="material-design">🎨 {$i18n.t('Material Design')}</option>
						<!-- <option value="rose-pine dark">🪻 {$i18n.t('Rosé Pine')}</option>
						<option value="rose-pine-dawn light">🌷 {$i18n.t('Rosé Pine Dawn')}</option> -->
					</select>
				</div>
			</div>

			<div class=" flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Language')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent text-right {$settings.highContrastMode
							? ''
							: 'outline-hidden'}"
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
			{#if $i18n.language === 'en-US'}
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
					<div class=" self-center text-xs font-medium">{$i18n.t('Notifications')}</div>

					<button
						class="p-1 px-3 text-xs flex rounded-sm transition"
						on:click={() => {
							toggleNotification();
						}}
						type="button"
					>
						{#if notificationEnabled === true}
							<span class="ml-2 self-center">{$i18n.t('On')}</span>
						{:else}
							<span class="ml-2 self-center">{$i18n.t('Off')}</span>
						{/if}
					</button>
				</div>
			</div>
			
			<div class=" py-0.5 flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Show User Gravatar')}</div>
				<label class="relative inline-flex items-center cursor-pointer">
					<input
						type="checkbox"
						bind:checked={showUserGravatar}
						class="sr-only peer"
						on:change={() => {
							saveSettings({ showUserGravatar: showUserGravatar });
						}}
					/>
					<div
						class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"
					></div>
				</label>
			</div>
		</div>

		{#if $user?.role === 'admin' || ($user?.permissions?.chat?.system_prompt ?? true)}
			<hr class="border-gray-50 dark:border-gray-850 my-3" />

			<div>
				<div class=" my-2.5 text-sm font-medium">{$i18n.t('System Prompt')}</div>
				<Textarea
					bind:value={system}
					className={'w-full text-sm outline-hidden resize-vertical' +
						($settings.highContrastMode
							? ' p-2.5 border-2 border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-850 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 overflow-y-hidden'
							: ' bg-white dark:text-gray-300 dark:bg-gray-900')}
					rows={4}
					placeholder={$i18n.t('Enter system prompt here')}
				/>
			</div>
		{/if}

		{#if $user?.role === 'admin' || ($user?.permissions?.chat?.controls ?? true)}
			<div class="mt-2 space-y-3 pr-1.5">
				<div class="flex justify-between items-center text-sm">
					<div class="  font-medium">{$i18n.t('Advanced Parameters')}</div>
					<button
						class=" text-xs font-medium text-gray-500"
						type="button"
						on:click={() => {
							showAdvanced = !showAdvanced;
						}}>{showAdvanced ? $i18n.t('Hide') : $i18n.t('Show')}</button
					>
				</div>

				{#if showAdvanced}
					<div
						in:slideAndFade={{ delay: 100 }}
						out:slideAndFade
					>
						<AdvancedParams
							admin={$user?.role === 'admin'}
							params={advancedParams}
							on:change={(e) => {
								advancedParams = e.detail;
							}}
						/>
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
			{$i18n.t('Save')}
		</button>
	</div>
</div>
