<script lang="ts">
	import { config, models, settings, user } from '$lib/stores';
	import { createEventDispatcher, onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	import { updateUserInfo } from '$lib/apis/users';
	import { getUserPosition } from '$lib/utils';
	import i18n from '$lib/i18n';
	import type { Settings } from '$lib/stores';

	import FloppyDisk from '$lib/components/icons/FloppyDisk.svelte';
	const dispatch = createEventDispatcher();

	let t = $i18n.t.bind($i18n);
	$: t = $i18n.t.bind($i18n);

	export let saveSettings: (settings: Partial<Settings>) => void;

	let backgroundImageUrl: string | null = null;
	let inputFiles: FileList | null = null;
	let filesInputElement: HTMLInputElement;
	let backgroundImageUrlInput = '';
	let showUrlInput = false;



	// Addons
	let titleAutoGenerate = true;
	let autoFollowUps = true;
	let autoTags = true;

	let responseAutoCopy = false;
	let widescreenMode = false;
	let splitLargeChunks = false;
	let scrollOnBranchChange = true;
	let userLocation = false;

	// Interface
	let defaultModelId = '';
	let showUsername = false;

	let notificationSound = true;
	let notificationSoundAlways = false;

	let highContrastMode = false;

	let detectArtifacts = true;

	let richTextInput = true;
	let insertPromptAsRichText = false;
	let promptAutocomplete = false;

	let largeTextAsFile = false;

	let keepFollowUpPrompts = false;
	let insertFollowUpPrompt = false;

	let landingPageMode = '';
	let chatBubble = true;
	let chatDirection: 'LTR' | 'RTL' | 'auto' = 'auto';
	let ctrlEnterToSend = false;
	let copyFormatted = false;

	let chatFadeStreamingText = true;
	let collapseCodeBlocks = false;
	let expandDetails = false;

	let imageCompression = false;
	let imageCompressionSize: { width: number | string; height: number | string } = {
		width: '',
		height: ''
	};

	// chat export
	let stylizedPdfExport = true;

	// Admin - Show Update Available Toast
	let showUpdateToast = true;
	let showChangelog = true;

	let showEmojiInCall = false;
	let voiceInterruption = false;
	let hapticFeedback = false;

	let webSearch: string | null = null;

	let iframeSandboxAllowSameOrigin = false;
	let iframeSandboxAllowForms = false;

	const toggleExpandDetails = () => {
		expandDetails = !expandDetails;
		saveSettings({ expandDetails });
	};

	const toggleCollapseCodeBlocks = () => {
		collapseCodeBlocks = !collapseCodeBlocks;
		saveSettings({ collapseCodeBlocks });
	};

	const toggleSplitLargeChunks = async () => {
		splitLargeChunks = !splitLargeChunks;
		saveSettings({ splitLargeChunks: splitLargeChunks });
	};

	const toggleHighContrastMode = async () => {
		highContrastMode = !highContrastMode;
		saveSettings({ highContrastMode: highContrastMode });
	};

	const togglePromptAutocomplete = async () => {
		promptAutocomplete = !promptAutocomplete;
		saveSettings({ promptAutocomplete: promptAutocomplete });
	};

	const toggleScrollOnBranchChange = async () => {
		scrollOnBranchChange = !scrollOnBranchChange;
		saveSettings({ scrollOnBranchChange: scrollOnBranchChange });
	};

	const toggleWidescreenMode = async () => {
		widescreenMode = !widescreenMode;
		saveSettings({ widescreenMode: widescreenMode });
	};

	const toggleChatBubble = async () => {
		chatBubble = !chatBubble;
		saveSettings({ chatBubble: chatBubble });
	};

	const toggleLandingPageMode = async () => {
		landingPageMode = landingPageMode === '' ? 'chat' : '';
		saveSettings({ landingPageMode: landingPageMode });
	};

	const toggleShowUpdateToast = async () => {
		showUpdateToast = !showUpdateToast;
		saveSettings({ showUpdateToast: showUpdateToast });
	};

	const toggleNotificationSound = async () => {
		notificationSound = !notificationSound;
		saveSettings({ notificationSound: notificationSound });
	};

	const toggleNotificationSoundAlways = async () => {
		notificationSoundAlways = !notificationSoundAlways;
		saveSettings({ notificationSoundAlways: notificationSoundAlways });
	};

	const toggleShowChangelog = async () => {
		showChangelog = !showChangelog;
		saveSettings({ showChangelog: showChangelog });
	};

	const toggleShowUsername = async () => {
		showUsername = !showUsername;
		saveSettings({ showUsername: showUsername });
	};

	const toggleEmojiInCall = async () => {
		showEmojiInCall = !showEmojiInCall;
		saveSettings({ showEmojiInCall: showEmojiInCall });
	};

	const toggleVoiceInterruption = async () => {
		voiceInterruption = !voiceInterruption;
		saveSettings({ voiceInterruption: voiceInterruption });
	};

	const toggleImageCompression = async () => {
		imageCompression = !imageCompression;
		saveSettings({ imageCompression });
	};

	const toggleChatFadeStreamingText = async () => {
		chatFadeStreamingText = !chatFadeStreamingText;
		saveSettings({ chatFadeStreamingText: chatFadeStreamingText });
	};

	const toggleHapticFeedback = async () => {
		hapticFeedback = !hapticFeedback;
		saveSettings({ hapticFeedback: hapticFeedback });
	};

	const toggleStylizedPdfExport = async () => {
		stylizedPdfExport = !stylizedPdfExport;
		saveSettings({ stylizedPdfExport: stylizedPdfExport });
	};

	const toggleUserLocation = async () => {
		userLocation = !userLocation;

		if (userLocation) {
			const position = await getUserPosition().catch((error) => {
				toast.error(error.message);
				return null;
			});

			if (position) {
				await updateUserInfo(localStorage.token, { location: position });
				toast.success(t('User location successfully retrieved.'));
			} else {
				userLocation = false;
			}
		}

		saveSettings({ userLocation });
	};

	const toggleTitleAutoGenerate = async () => {
		titleAutoGenerate = !titleAutoGenerate;
		saveSettings({
			title: {
				...$settings.title,
				auto: titleAutoGenerate
			}
		});
	};

	const toggleAutoFollowUps = async () => {
		autoFollowUps = !autoFollowUps;
		saveSettings({ autoFollowUps });
	};

	const toggleAutoTags = async () => {
		autoTags = !autoTags;
		saveSettings({ autoTags });
	};

	const toggleDetectArtifacts = async () => {
		detectArtifacts = !detectArtifacts;
		saveSettings({ detectArtifacts });
	};

	const toggleRichTextInput = async () => {
		richTextInput = !richTextInput;
		saveSettings({ richTextInput });
	};

	const toggleInsertPromptAsRichText = async () => {
		insertPromptAsRichText = !insertPromptAsRichText;
		saveSettings({ insertPromptAsRichText });
	};

	const toggleKeepFollowUpPrompts = async () => {
		keepFollowUpPrompts = !keepFollowUpPrompts;
		saveSettings({ keepFollowUpPrompts });
	};

	const toggleInsertFollowUpPrompt = async () => {
		insertFollowUpPrompt = !insertFollowUpPrompt;
		saveSettings({ insertFollowUpPrompt });
	};

	const toggleLargeTextAsFile = async () => {
		largeTextAsFile = !largeTextAsFile;
		saveSettings({ largeTextAsFile });
	};

	const toggleResponseAutoCopy = async () => {
		const permission = await navigator.clipboard
			.readText()
			.then(() => {
				return 'granted';
			})
			.catch(() => {
				return '';
			});

		console.log(permission);

		if (permission === 'granted') {
			responseAutoCopy = !responseAutoCopy;
			saveSettings({ responseAutoCopy: responseAutoCopy });
		} else {
			toast.error(
				t(
					'Clipboard write permission denied. Please check your browser settings to grant the necessary access.'
				)
			);
		}
	};

	const toggleCopyFormatted = async () => {
		copyFormatted = !copyFormatted;
		saveSettings({ copyFormatted });
	};

	const toggleChangeChatDirection = async () => {
		if (chatDirection === 'auto') {
			chatDirection = 'LTR';
		} else if (chatDirection === 'LTR') {
			chatDirection = 'RTL';
		} else if (chatDirection === 'RTL') {
			chatDirection = 'auto';
		}
		saveSettings({ chatDirection });
	};

	const toggleCtrlEnterToSend = async () => {
		ctrlEnterToSend = !ctrlEnterToSend;
		saveSettings({ ctrlEnterToSend });
	};

	const updateInterfaceHandler = async () => {
		saveSettings({
			models: [defaultModelId],
			imageCompressionSize: imageCompressionSize
		});
	};

	const toggleWebSearch = async () => {
		webSearch = webSearch === null ? 'always' : null;
		saveSettings({ webSearch: webSearch });
	};

	const toggleIframeSandboxAllowSameOrigin = async () => {
		iframeSandboxAllowSameOrigin = !iframeSandboxAllowSameOrigin;
		saveSettings({ iframeSandboxAllowSameOrigin });
	};

	const toggleIframeSandboxAllowForms = async () => {
		iframeSandboxAllowForms = !iframeSandboxAllowForms;
		saveSettings({ iframeSandboxAllowForms });
	};

	const setBackgroundImageFromUrl = () => {
		if (backgroundImageUrlInput.trim()) {
			backgroundImageUrl = backgroundImageUrlInput.trim();
			saveSettings({ backgroundImageUrl });
			backgroundImageUrlInput = '';
			showUrlInput = false;
		}
	};



	const toggleUrlInput = () => {
		showUrlInput = !showUrlInput;
		if (!showUrlInput) {
			backgroundImageUrlInput = '';
		}
	};

	onMount(async () => {
		titleAutoGenerate = $settings?.title?.auto ?? true;
		autoTags = $settings?.autoTags ?? true;
		autoFollowUps = $settings?.autoFollowUps ?? true;

		highContrastMode = $settings?.highContrastMode ?? false;

		detectArtifacts = $settings?.detectArtifacts ?? true;
		responseAutoCopy = $settings?.responseAutoCopy ?? false;

		showUsername = $settings?.showUsername ?? false;
		showUpdateToast = $settings?.showUpdateToast ?? true;
		showChangelog = $settings?.showChangelog ?? true;

		showEmojiInCall = $settings?.showEmojiInCall ?? false;
		voiceInterruption = $settings?.voiceInterruption ?? false;

		chatFadeStreamingText = $settings?.chatFadeStreamingText ?? true;

		richTextInput = $settings?.richTextInput ?? true;
		insertPromptAsRichText = $settings?.insertPromptAsRichText ?? false;
		promptAutocomplete = $settings?.promptAutocomplete ?? false;

		keepFollowUpPrompts = $settings?.keepFollowUpPrompts ?? false;
		insertFollowUpPrompt = $settings?.insertFollowUpPrompt ?? false;

		largeTextAsFile = $settings?.largeTextAsFile ?? false;
		copyFormatted = $settings?.copyFormatted ?? false;

		collapseCodeBlocks = $settings?.collapseCodeBlocks ?? false;
		expandDetails = $settings?.expandDetails ?? false;

		landingPageMode = $settings?.landingPageMode ?? '';
		chatBubble = $settings?.chatBubble ?? true;
		widescreenMode = $settings?.widescreenMode ?? false;
		splitLargeChunks = $settings?.splitLargeChunks ?? false;
		scrollOnBranchChange = $settings?.scrollOnBranchChange ?? true;
		chatDirection = $settings?.chatDirection ?? 'auto';
		userLocation = $settings?.userLocation ?? false;

		notificationSound = $settings?.notificationSound ?? true;
		notificationSoundAlways = $settings?.notificationSoundAlways ?? false;

		iframeSandboxAllowSameOrigin = $settings?.iframeSandboxAllowSameOrigin ?? false;
		iframeSandboxAllowForms = $settings?.iframeSandboxAllowForms ?? false;

		stylizedPdfExport = $settings?.stylizedPdfExport ?? true;

		hapticFeedback = $settings?.hapticFeedback ?? false;
		ctrlEnterToSend = $settings?.ctrlEnterToSend ?? false;

		imageCompression = $settings?.imageCompression ?? false;
		imageCompressionSize = $settings?.imageCompressionSize ?? { width: '', height: '' };

		defaultModelId = $settings?.models?.at(0) ?? '';
		if ($config?.default_models) {
			defaultModelId = $config.default_models.split(',')[0];
		}

		backgroundImageUrl = $settings?.backgroundImageUrl ?? null;
		webSearch = $settings?.webSearch ?? null;
	});
</script>

<div class="flex flex-col h-full">
	<input
		bind:this={filesInputElement}
		bind:files={inputFiles}
		type="file"
		hidden
		accept="image/*,video/mp4"
		on:change={() => {
			if (inputFiles && inputFiles.length > 0) {
				const reader = new FileReader();
				reader.onload = (e) => {
					if (e.target?.result) {
						backgroundImageUrl = e.target.result.toString();
						saveSettings({ backgroundImageUrl });
					}
				};

				if (['image/gif', 'image/webp', 'image/jpeg', 'image/png', 'video/mp4'].includes(inputFiles[0].type)) {
					reader.readAsDataURL(inputFiles[0]);
				} else {
					console.log(`Unsupported File Type '${inputFiles[0].type}'.`);
					inputFiles = null;
				}
			}
		}}
	/>
	<div class="px-4 py-3 border-b border-gray-100 dark:border-gray-800">
		<h1 class=" text-lg font-medium">{$i18n.t('UI')}</h1>
	</div>

	<div class=" flex-1 overflow-y-auto p-4 space-y-4">
		<div class="space-y-2">
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('High Contrast Mode')} ({$i18n.t('Beta')})</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {highContrastMode
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleHighContrastMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!highContrastMode
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleHighContrastMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Landing Page Mode')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {landingPageMode !== 'chat'
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleLandingPageMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Default')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {landingPageMode === 'chat'
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleLandingPageMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Chat')}</span>
					</button>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Chat Bubble UI')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {chatBubble
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleChatBubble();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!chatBubble
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleChatBubble();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class="flex-1 self-center text-xs">
					<div>{$i18n.t('Display the username instead of You in the Chat')}</div>
					<div class=" text-gray-500 text-xs">{'Requires a page refresh to apply'}</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {showUsername
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowUsername();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!showUsername
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowUsername();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Widescreen Mode')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {widescreenMode
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleWidescreenMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!widescreenMode
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleWidescreenMode();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Chat direction')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {chatDirection === 'LTR'
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							chatDirection = 'LTR';
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('LTR')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {chatDirection === 'RTL'
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							chatDirection = 'RTL';
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('RTL')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {chatDirection === 'auto'
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							chatDirection = 'auto';
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Auto')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Notification Sound')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {notificationSound
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleNotificationSound();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!notificationSound
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleNotificationSound();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class="flex-1">
					<div class=" self-center text-xs">{$i18n.t('Always Play Notification Sound')}</div>
					<div class=" text-gray-500 text-xs">
						{'Play notification sound even if the tab is active'}
					</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {notificationSoundAlways
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleNotificationSoundAlways();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!notificationSoundAlways
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleNotificationSoundAlways();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class="flex-1">
					<div class=" self-center text-xs">
						{$i18n.t('Toast notifications for new updates')}
					</div>
					<div class=" text-gray-500 text-xs">
						{'Receive a toast notification when a new update is available'}
					</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {showUpdateToast
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowUpdateToast();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!showUpdateToast
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowUpdateToast();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class="flex-1">
					<div class=" self-center text-xs">{$i18n.t(`Show "What's New" modal on login`)}</div>
					<div class=" text-gray-500 text-xs">
						{'Display new features and updates when you log in'}
					</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {showChangelog
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowChangelog();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!showChangelog
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleShowChangelog();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
		</div>

		<div class="space-y-2">
			<div class=" my-1.5 text-sm font-medium">{$i18n.t('Chat')}</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Title Auto-Generation')}</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {titleAutoGenerate
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleTitleAutoGenerate();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!titleAutoGenerate
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleTitleAutoGenerate();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Follow-Up Auto-Generation')}</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {autoFollowUps
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleAutoFollowUps();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!autoFollowUps
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleAutoFollowUps();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Chat Tags Auto-Generation')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {autoTags
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleAutoTags();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!autoTags
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleAutoTags();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Detect Artifacts Automatically')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {detectArtifacts
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleDetectArtifacts();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!detectArtifacts
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleDetectArtifacts();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Auto-Copy Response to Clipboard')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {responseAutoCopy
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleResponseAutoCopy();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!responseAutoCopy
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleResponseAutoCopy();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Fade Effect for Streaming Text')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {chatFadeStreamingText
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleChatFadeStreamingText();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!chatFadeStreamingText
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleChatFadeStreamingText();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Keep Follow-Up Prompts in Chat')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {keepFollowUpPrompts
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleKeepFollowUpPrompts();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!keepFollowUpPrompts
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleKeepFollowUpPrompts();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Insert Follow-Up Prompt to Input')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {insertFollowUpPrompt
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleInsertFollowUpPrompt();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!insertFollowUpPrompt
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleInsertFollowUpPrompt();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Rich Text Input for Chat')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {richTextInput
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleRichTextInput();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!richTextInput
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleRichTextInput();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class="flex-1">
					<div class=" self-center text-xs">{$i18n.t('Insert Prompt as Rich Text')}</div>
					<div class=" text-gray-500 text-xs">{'Requires Rich Text Input to be enabled'}</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {insertPromptAsRichText
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleInsertPromptAsRichText();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!insertPromptAsRichText
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleInsertPromptAsRichText();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class="flex-1">
					<div class=" self-center text-xs">{$i18n.t('Prompt Autocompletion')}</div>
					<div class=" text-gray-500 text-xs">{'Press Tab to complete prompts.'}</div>
				</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {promptAutocomplete
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							togglePromptAutocomplete();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!promptAutocomplete
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							togglePromptAutocomplete();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Paste Large Text as File')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {largeTextAsFile
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleLargeTextAsFile();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!largeTextAsFile
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleLargeTextAsFile();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Copy Formatted Text')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {copyFormatted
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCopyFormatted();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!copyFormatted
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCopyFormatted();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Always Collapse Code Blocks')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {collapseCodeBlocks
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCollapseCodeBlocks();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!collapseCodeBlocks
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCollapseCodeBlocks();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Always Expand Details')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {expandDetails
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleExpandDetails();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!expandDetails
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleExpandDetails();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Chat Background Image')}</div>
				<div class="self-center flex space-x-2">
					<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
						{#if backgroundImageUrl !== null}
							<Tooltip content={'Reset'}>
								<button
									class=" text-xs px-2 py-1 flex-1 rounded-md transition-all hover:bg-white dark:hover:bg-gray-700"
									on:click={() => {
										backgroundImageUrl = null;
										saveSettings({ backgroundImageUrl: null });
									}}
								>
									<span class="ml-2 self-center">{$i18n.t('Reset')}</span>
								</button>
							</Tooltip>
						{/if}
						<Tooltip content={'Upload'}>
							<button
								class=" text-xs px-2 py-1 flex-1 rounded-md transition-all hover:bg-white dark:hover:bg-gray-700"
								on:click={() => {
									filesInputElement.click();
								}}
							>
								<span class="ml-2 self-center">{$i18n.t('Upload')}</span>
							</button>
						</Tooltip>

						<Tooltip content={'URL'}>
							<button
								class=" text-xs px-2 py-1 flex-1 rounded-md transition-all hover:bg-white dark:hover:bg-gray-700"
								on:click={() => {
									showUrlInput = true;
								}}
							>
								<span class="ml-2 self-center">{$i18n.t('URL')}</span>
							</button>
						</Tooltip>
					</div>
				</div>
			</div>

			{#if showUrlInput}
				<div class="flex items-center justify-between">
					<div class=" self-center text-xs">{'Image URL'}</div>
					<div class=" self-center flex space-x-2">
						<input
							class="w-full"
							type="text"
							placeholder={$i18n.t('Enter image/video URL')}
							bind:value={backgroundImageUrlInput}
							on:keydown={(e) => {
								if (e.key === 'Enter') {
									setBackgroundImageFromUrl();
									showUrlInput = false;
								}
							}}
						/>
						<div
							class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5"
							role="group"
						>
							<button
								class=" text-xs px-2 py-1 flex-1 rounded-md transition-all bg-white dark:bg-gray-700 shadow"
								on:click={() => {
									setBackgroundImageFromUrl();
									showUrlInput = false;
								}}
							>
								{$i18n.t('Set')}
							</button>
							<button
								class=" text-xs px-2 py-1 flex-1 rounded-md transition-all"
								on:click={() => {
									showUrlInput = false;
								}}
							>
								{$i18n.t('Cancel')}
							</button>
						</div>
					</div>
				</div>
			{/if}


			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Allow User Location')}</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {userLocation
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleUserLocation();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!userLocation
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleUserLocation();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Haptic Feedback')} ({$i18n.t('Android')})</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {hapticFeedback
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleHapticFeedback();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!hapticFeedback
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleHapticFeedback();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>

			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Enter Key Behavior')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {ctrlEnterToSend
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCtrlEnterToSend();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Ctrl+Enter to Send')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!ctrlEnterToSend
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleCtrlEnterToSend();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Enter to Send')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Scroll On Branch Change')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {scrollOnBranchChange
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleScrollOnBranchChange();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!scrollOnBranchChange
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleScrollOnBranchChange();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Web Search in Chat')}</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all"
						class:bg-white={webSearch === null}
						class:dark:bg-gray-700={webSearch === null}
						class:shadow={webSearch === null}
						on:click={toggleWebSearch}
					>
						{#if webSearch === 'always'}
							<span class="ml-2 self-center">{$i18n.t('Always')}</span>
						{:else}
							<span class="ml-2 self-center">{$i18n.t('Default')}</span>
						{/if}
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('iframe Sandbox Allow Same Origin')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {iframeSandboxAllowSameOrigin
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleIframeSandboxAllowSameOrigin();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!iframeSandboxAllowSameOrigin
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleIframeSandboxAllowSameOrigin();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('iframe Sandbox Allow Forms')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {iframeSandboxAllowForms
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleIframeSandboxAllowForms();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!iframeSandboxAllowForms
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleIframeSandboxAllowForms();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Stylized PDF Export')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {stylizedPdfExport
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleStylizedPdfExport();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!stylizedPdfExport
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleStylizedPdfExport();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
		</div>
		<div class="space-y-2">
			<div class=" my-1.5 text-sm font-medium">{$i18n.t('Voice')}</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Allow Voice Interruption in Call')}</div>

				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {voiceInterruption
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleVoiceInterruption();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!voiceInterruption
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleVoiceInterruption();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Display Emoji in Call')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {showEmojiInCall
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleEmojiInCall();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!showEmojiInCall
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleEmojiInCall();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
		</div>
		<div class="space-y-2">
			<div class=" my-1.5 text-sm font-medium">{$i18n.t('File')}</div>
			<div class="flex items-center justify-between">
				<div class=" self-center text-xs">{$i18n.t('Image Compression')}</div>
				<div class=" self-center flex rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5" role="group">
					<button
						class=" text-xs px-2 py-1 flex-1 rounded-md transition-all {imageCompression
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleImageCompression();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('On')}</span>
					</button>
					<button
						class="text-xs px-2 py-1 flex-1 rounded-md transition-all {!imageCompression
							? ' bg-white dark:bg-gray-700 shadow'
							: ''}"
						on:click={() => {
							toggleImageCompression();
						}}
					>
						<span class="ml-2 self-center">{$i18n.t('Off')}</span>
					</button>
				</div>
			</div>
			{#if imageCompression}
				<div class="flex items-center justify-between">
					<div class=" self-center text-xs">{$i18n.t('Image Max Compression Size')}</div>
					<div class=" self-center flex space-x-2">
						<div class="max-w-24">
							<label class="text-xs text-gray-500" for="image-compression-width"
								>{$i18n.t('Image Max Compression Size width')}</label
							>
							<input
								id="image-compression-width"
								class="w-full"
								type="number"
								placeholder="1024"
								bind:value={imageCompressionSize.width}
							/>
						</div>
						<div class="max-w-24">
							<label class="text-xs text-gray-500" for="image-compression-height"
								>{$i18n.t('Image Max Compression Size height')}</label
							>
							<input
								id="image-compression-height"
								class="w-full"
								type="number"
								placeholder="1024"
								bind:value={imageCompressionSize.height}
							/>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<div class=" p-4 border-t border-gray-100 dark:border-gray-800">
		<button
			type="button"
			class=" w-full"
			on:click={() => {
				dispatch('save');
			}}
		>
			<FloppyDisk className="w-4 h-4 mr-2" />
			{$i18n.t('Save')}
		</button>
	</div>
</div>
