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

	import { settings, theme, user } from '$lib/stores';
	import {
		generateThemeFromBackground,
		applyMaterialTheme,
		removeMaterialTheme
	} from '$lib/utils/materialThemeGenerator';
	import { themeManager } from '$lib/utils/themeManager';
	import { clearModelsCache } from '$lib/apis';

	const i18n = getContext('i18n') as Readable<i18nType>;

	import AdvancedParams, {
		defaultParams
	} from '$lib/components/chat/Settings/Advanced/AdvancedParams.svelte';
	import Textarea from '$lib/components/common/Textarea.svelte';
	export let saveSettings: Function;
	export const getModels: Function = () => {}; // External reference for parent component

	// General
	let selectedTheme = 'system';

	let languages: Awaited<ReturnType<typeof getLanguages>> = [];
	let lang = get(i18n).language;
	let notificationEnabled = false;
	let showUserGravatar = false;
	let materialThemeEnabled = false;
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

	const refreshModelsCache = async () => {
		try {
			clearModelsCache();
			// Refresh models by calling getModels with refresh=true
			await getModels();
			toast.success(get(i18n).t('Models cache refreshed successfully!'));
		} catch (error) {
			console.error('Error refreshing models cache:', error);
			toast.error(get(i18n).t('Failed to refresh models cache'));
		}
	};

	// Reactive statement to ensure theme changes are applied immediately
	$: if (selectedTheme) {
		// Only apply through applyTheme if it's not Material Design
		// Material Design is handled by the themeChangeHandler
		if (selectedTheme !== 'material-design') {
			applyTheme(selectedTheme);
		}
	}

	// Reactive statement to handle Material Design theme when theme store changes
	$: if ($theme === 'material-design' && materialThemeEnabled) {
		const backgroundImageUrl = $settings?.backgroundImageUrl;
		if (backgroundImageUrl) {
			generateThemeFromBackground(backgroundImageUrl)
				.then((palette) => {
					applyMaterialTheme(palette);
				})
				.catch((error) => {
					console.error('Failed to generate Material Design theme:', error);
					// Apply default macaron theme
					applyMaterialTheme({
						primary: '#FFB6C1', // Light Pink (macaron pink)
						primaryVariant: '#FF91A4', // Deeper Pink
						secondary: '#B8E6B8', // Mint Green (macaron green)
						secondaryVariant: '#98D982', // Deeper Mint
						background: '#FFF8F0', // Cream (macaron cream)
						surface: '#FFFFFF', // White
						error: '#FFB3BA', // Soft Red (macaron red)
						onPrimary: '#FFFFFF', // White text on primary
						onSecondary: '#2D5016', // Dark green text on secondary
						onBackground: '#5D4E37', // Brown text on background
						onSurface: '#5D4E37', // Brown text on surface
						onError: '#8B0000' // Dark red text on error
					});
				});
		} else {
			// Apply default macaron theme when no background image
			applyMaterialTheme({
				primary: '#FFB6C1', // Light Pink (macaron pink)
				primaryVariant: '#FF91A4', // Deeper Pink
				secondary: '#B8E6B8', // Mint Green (macaron green)
				secondaryVariant: '#98D982', // Deeper Mint
				background: '#FFF8F0', // Cream (macaron cream)
				surface: '#FFFFFF', // White
				error: '#FFB3BA', // Soft Red (macaron red)
				onPrimary: '#FFFFFF', // White text on primary
				onSecondary: '#2D5016', // Dark green text on secondary
				onBackground: '#5D4E37', // Brown text on background
				onSurface: '#5D4E37', // Brown text on surface
				onError: '#8B0000' // Dark red text on error
			});
		}
	} else if ($theme !== 'material-design' || !materialThemeEnabled) {
		// Remove Material Design theme when switching to other themes or when disabled
		removeMaterialTheme();
	}

	onMount(async () => {
		selectedTheme = localStorage.theme ?? 'system';
		applyTheme(selectedTheme);

		languages = await getLanguages();

		notificationEnabled = $settings.notificationEnabled ?? false;
		showUserGravatar = $settings.showUserGravatar ?? false;
		materialThemeEnabled = $settings.materialThemeEnabled ?? false;
		system = $settings.system ?? '';

		advancedParams = { ...advancedParams, ...$settings.params };
		advancedParams.stop = $settings?.params?.stop
			? ($settings?.params?.stop ?? []).join(',')
			: null;
	});

	const applyTheme = (_theme: string) => {
		// For Material Design, we handle it separately to avoid conflicts
		if (_theme === 'material-design') {
			// Clear existing theme classes first
			document.documentElement.classList.remove(
				'dark',
				'light',
				'oled-dark',
				'rose-pine',
				'her',
				'frosted-glass',
				'md-theme'
			);
			// Material Design theme will be applied by the themeChangeHandler
			return;
		}
		// Use the new ThemeManager for other themes
		themeManager.applyTheme(_theme);
	};

	const themeChangeHandler = async (_theme: string) => {
		theme.set(_theme);
		localStorage.setItem('theme', _theme);
		applyTheme(_theme);

		// Handle Material Design theme
		if (_theme === 'material-design' || _theme === 'material-design-transparent') {
			// Clear existing theme classes and apply Material Design base
			document.documentElement.classList.remove('dark', 'light', 'oled-dark', 'rose-pine', 'her', 'frosted-glass', 'transparent');
			document.documentElement.classList.add('md-theme');

			// Add transparent class for transparent variant
			if (_theme === 'material-design-transparent') {
				document.documentElement.classList.add('transparent');
			}

			// Update meta theme color
			const metaThemeColor = document.querySelector('meta[name="theme-color"]');
			if (metaThemeColor) {
				const themeColor = _theme === 'material-design-transparent' ? 'rgba(255, 182, 193, 0.8)' : '#FFB6C1';
				metaThemeColor.setAttribute('content', themeColor);
			}

			// Only apply Material Design theme if it's explicitly enabled
			if (materialThemeEnabled) {
				const backgroundImageUrl = $settings?.backgroundImageUrl;
				if (backgroundImageUrl) {
					try {
						const palette = await generateThemeFromBackground(backgroundImageUrl);
						applyMaterialTheme(palette);
					} catch (error) {
						console.error('Failed to generate Material Design theme:', error);
						// Apply default Material Design theme with macaron colors
						applyMaterialTheme({
							primary: '#FFB6C1', // Light Pink (macaron pink)
							primaryVariant: '#FF91A4', // Deeper Pink
							secondary: '#B8E6B8', // Mint Green (macaron green)
							secondaryVariant: '#98D982', // Deeper Mint
							background: '#FFF8F0', // Cream (macaron cream)
							surface: '#FFFFFF', // White
							error: '#FFB3BA', // Soft Red (macaron red)
							onPrimary: '#FFFFFF', // White text on primary
							onSecondary: '#2D5016', // Dark green text on secondary
							onBackground: '#5D4E37', // Brown text on background
							onSurface: '#5D4E37', // Brown text on surface
							onError: '#8B0000' // Dark red text on error
						});
					}
				} else {
					// Apply default Material Design theme with macaron colors when no background image
					applyMaterialTheme({
						primary: '#FFB6C1', // Light Pink (macaron pink)
						primaryVariant: '#FF91A4', // Deeper Pink
						secondary: '#B8E6B8', // Mint Green (macaron green)
						secondaryVariant: '#98D982', // Deeper Mint
						background: '#FFF8F0', // Cream (macaron cream)
						surface: '#FFFFFF', // White
						error: '#FFB3BA', // Soft Red (macaron red)
						onPrimary: '#FFFFFF', // White text on primary
						onSecondary: '#2D5016', // Dark green text on secondary
						onBackground: '#5D4E37', // Brown text on background
						onSurface: '#5D4E37', // Brown text on surface
						onError: '#8B0000' // Dark red text on error
					});
				}
			} else {
				// When Material Design is disabled, just apply basic theme classes without custom colors
				// This provides a clean Material Design look without auto-generation
			}
		} else {
			// Remove Material Design theme when switching to other themes
			removeMaterialTheme();
		}
	};

	const toggleMaterialTheme = async () => {
		materialThemeEnabled = !materialThemeEnabled;
		saveSettings({ materialThemeEnabled });

		if (materialThemeEnabled && selectedTheme === 'material-design') {
			// Apply macaron theme when enabled
			const macaronPalette = {
				primary: '#FFB6C1', // Light Pink (macaron pink)
				primaryVariant: '#FF91A4', // Deeper Pink
				secondary: '#B8E6B8', // Mint Green (macaron green)
				secondaryVariant: '#98D982', // Deeper Mint
				background: '#FFF8F0', // Cream (macaron cream)
				surface: '#FFFFFF', // White
				error: '#FFB3BA', // Soft Red (macaron red)
				onPrimary: '#FFFFFF', // White text on primary
				onSecondary: '#2D5016', // Dark green text on secondary
				onBackground: '#5D4E37', // Brown text on background
				onSurface: '#5D4E37', // Brown text on surface
				onError: '#8B0000' // Dark red text on error
			};
			applyMaterialTheme(macaronPalette);
		} else if (!materialThemeEnabled) {
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
						<option value="rose-pine">🪻 {$i18n.t('Rosé Pine')}</option>
						<option value="her">🌷 Her</option>
						<option value="material-design">🎨 {$i18n.t('Material Design')}</option>
						<option value="material-design-transparent">🎨✨ {$i18n.t('Material Design (Transparent)')}</option>
						<option value="frosted-glass">❄️ {$i18n.t('Frosted Glass')}</option>
					</select>
				</div>
			</div>

			{#if selectedTheme === 'material-design' || selectedTheme === 'material-design-transparent'}
				<div class="flex items-center justify-between">
					<div class=" self-center text-xs">{$i18n.t('Material Design Theme')}</div>
					<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
						<button
							class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {materialThemeEnabled
								? ' bg-white dark:bg-gray-700 shadow'
								: ''}"
							on:click={() => {
								toggleMaterialTheme();
							}}
						>
							<span class="ml-2 self-center">{$i18n.t('On')}</span>
						</button>
						<button
							class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!materialThemeEnabled
								? ' bg-white dark:bg-gray-700 shadow'
								: ''}"
							on:click={() => {
								toggleMaterialTheme();
							}}
						>
							<span class="ml-2 self-center">{$i18n.t('Off')}</span>
						</button>
					</div>
				</div>
			{/if}

			<div class=" flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Language')}</div>
				<div class="flex items-center relative">
					<select
						class="dark:bg-gray-900 w-fit pr-8 rounded-sm py-2 px-2 text-xs bg-transparent text-right {$settings.highContrastMode
							? ''
							: 'outline-hidden'}"
						bind:value={lang}
						placeholder="Select a language"
						on:change={() => {
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

			<div class=" flex w-full justify-between">
				<div class=" self-center text-xs font-medium">{$i18n.t('Models Cache')}</div>
				<button
					class="p-1 px-3 text-xs flex rounded-sm transition bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700"
					on:click={refreshModelsCache}
					type="button"
					title={$i18n.t('Refresh models cache (cached for 1 day)')}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 16 16"
						fill="currentColor"
						class="w-3 h-3 mr-1.5"
					>
						<path
							fill-rule="evenodd"
							d="M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z"
						/>
					</svg>
					<span class="self-center">{$i18n.t('Refresh')}</span>
				</button>
			</div>
			<div class="mb-2 text-xs text-gray-400 dark:text-gray-500">
				{$i18n.t('Models are cached for 1 day to improve performance. Click refresh to update the cache manually.')}
			</div>

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
					<div in:slideAndFade={{ delay: 100 }} out:slideAndFade>
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
