<script lang="ts">
	import { getContext } from 'svelte';
	import Modal from '../common/Modal.svelte';
	import { toast } from 'svelte-sonner';

	import Tooltip from '../common/Tooltip.svelte';
	const i18n = getContext('i18n');
	import XMark from '$lib/components/icons/XMark.svelte';

	export let show = false;

	// Function to unmute all videos in the current window
	const unmuteAllVideos = () => {
		try {
			const videos = document.querySelectorAll('video');
			let unmuteCount = 0;

			videos.forEach((video) => {
				if (video.muted) {
					video.muted = false;
					unmuteCount++;
				}
			});

			if (unmuteCount > 0) {
				toast.success($i18n.t(`Unmuted {{count}} video(s)`, { count: unmuteCount }));
			} else {
				toast.info($i18n.t('No muted videos found'));
			}
		} catch (error) {
			console.error('Error unmuting videos:', error);
			toast.error($i18n.t('Failed to unmute videos'));
		}
	};

	// Function to play all videos in the current window
	const playAllVideos = () => {
		try {
			const videos = document.querySelectorAll('video');
			let playCount = 0;

			videos.forEach((video) => {
				video.play();
				playCount++;
			});

			if (playCount > 0) {
				toast.success($i18n.t(`Playing {{count}} video(s)`, { count: playCount }));
			} else {
				toast.info($i18n.t('No videos found to play'));
			}
		} catch (error) {
			console.error('Error playing videos:', error);
			toast.error($i18n.t('Failed to play videos'));
		}
	};

	// Function to pause all videos in the current window
	const pauseAllVideos = () => {
		try {
			const videos = document.querySelectorAll('video');
			let pauseCount = 0;

			videos.forEach((video) => {
				if (!video.paused) {
					video.pause();
					pauseCount++;
				}
			});

			if (pauseCount > 0) {
				toast.success($i18n.t(`Paused {{count}} video(s)`, { count: pauseCount }));
			} else {
				toast.info($i18n.t('No playing videos found to pause'));
			}
		} catch (error) {
			console.error('Error pausing videos:', error);
			toast.error($i18n.t('Failed to pause videos'));
		}
	};
</script>

<Modal bind:show>
	<div class="text-gray-700 dark:text-gray-100">
		<div class=" flex justify-between dark:text-gray-300 px-5 pt-4">
			<div class=" text-lg font-medium self-center">{$i18n.t('Keyboard shortcuts')}</div>
			<button
				class="self-center"
				on:click={() => {
					show = false;
				}}
			>
				<XMark className={'size-5'} />
			</button>
		</div>

		<div class="flex flex-col md:flex-row w-full p-5 md:space-x-4 dark:text-gray-200">
			<div class=" flex flex-col w-full sm:flex-row sm:justify-center sm:space-x-6">
				<div class="flex flex-col space-y-3 w-full self-start">
					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Open new chat')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								O
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Focus chat input')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Esc
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							<Tooltip
								content={$i18n.t(
									'Only active when the chat input is in focus and an LLM is generating a response.'
								)}
							>
								{$i18n.t('Stop Generating')}<span class="text-xs"> *</span>
							</Tooltip>
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Esc
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Copy last code block')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								;
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Copy last response')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								C
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							<Tooltip
								content={$i18n.t(
									'Only active when "Paste Large Text as File" setting is toggled on.'
								)}
							>
								{$i18n.t('Prevent file creation')}<span class="text-s"> *</span>
							</Tooltip>
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								V
							</div>
						</div>
					</div>
				</div>

				<div class="flex flex-col space-y-3 w-full self-start">
					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Generate prompt pair')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Enter
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Toggle search')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								K
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Toggle settings')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								.
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Toggle sidebar')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								S
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Delete chat')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								⌫/Delete
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Show shortcuts')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								/
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">{$i18n.t('Custom Styles')}</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Ctrl/⌘
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								Shift
							</div>

							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								S
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div class=" flex justify-between dark:text-gray-300 px-5 pt-4">
			<div class=" text-lg font-medium self-center">{$i18n.t('Other Actions')}</div>
		</div>

		<div class="flex flex-col md:flex-row w-full p-5 md:space-x-4 dark:text-gray-200">
			<div class="flex w-full space-x-2">
				<button
					class="w-full h-fit py-2 px-3 flex items-center justify-center rounded-lg border border-black/10 text-gray-800 dark:border-white/10 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
					on:click={unmuteAllVideos}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-5 h-5 mr-2"
					>
						<path
							d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 .898.121 1.768.348 2.595.341 1.24 1.518 1.905 2.66 1.905H6.44l4.5 4.5c.944.945 2.56.276 2.56-1.06V4.06zM18.584 12c0-1.857-.87-3.534-2.274-4.583-1.403-1.05-3.307-1.05-4.71 0-.31.233-.75.055-.75-.31V8.288c0-.366.44-.543.75-.31 2.298 1.723 3.726 4.335 3.726 7.245 0 2.909-1.428 5.522-3.726 7.245-.31.233-.75.055-.75-.31v-1.11c0-.366.44-.543.75-.31 1.403 1.05 3.307 1.05 4.71 0 1.404-1.05 2.274-2.726 2.274-4.583z"
						/>
					</svg>
					{$i18n.t('Unmute all videos')}
				</button>
				<button
					class="w-full h-fit py-2 px-3 flex items-center justify-center rounded-lg border border-black/10 text-gray-800 dark:border-white/10 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
					on:click={playAllVideos}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-5 h-5 mr-2"
					>
						<path
							fill-rule="evenodd"
							d="M4.5 5.653c0-1.426 1.529-2.33 2.779-1.643l11.54 6.647c1.295.748 1.295 2.538 0 3.286L7.279 20.99c-1.25.717-2.779-.217-2.779-1.643V5.653z"
							clip-rule="evenodd"
						/>
					</svg>
					{$i18n.t('Play all videos')}
				</button>
				<button
					class="w-full h-fit py-2 px-3 flex items-center justify-center rounded-lg border border-black/10 text-gray-800 dark:border-white/10 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
					on:click={pauseAllVideos}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="currentColor"
						class="w-5 h-5 mr-2"
					>
						<path
							fill-rule="evenodd"
							d="M6.75 5.25a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0V6a.75.75 0 01.75-.75zm9 0a.75.75 0 01.75.75v12a.75.75 0 01-1.5 0V6a.75.75 0 01.75-.75z"
							clip-rule="evenodd"
						/>
					</svg>
					{$i18n.t('Pause all videos')}
				</button>
			</div>
		</div>

		<div class="px-5 pb-4 text-xs text-gray-500 dark:text-gray-400">
			{$i18n.t(
				'Shortcuts with an asterisk (*) are situational and only active under specific conditions.'
			)}
		</div>
		<div class=" flex justify-between dark:text-gray-300 px-5">
			<div class=" text-lg font-medium self-center">{$i18n.t('Input commands')}</div>
		</div>

		<div class="flex flex-col md:flex-row w-full p-5 md:space-x-4 dark:text-gray-200">
			<div class=" flex flex-col w-full sm:flex-row sm:justify-center sm:space-x-6">
				<div class="flex flex-col space-y-3 w-full self-start">
					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							{$i18n.t('Attach file from knowledge')}
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								#
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							{$i18n.t('Add custom prompt')}
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								/
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							{$i18n.t('Talk to model')}
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								@
							</div>
						</div>
					</div>

					<div class="w-full flex justify-between items-center">
						<div class=" text-sm">
							{$i18n.t('Accept autocomplete generation / Jump to prompt variable')}
						</div>

						<div class="flex space-x-1 text-xs">
							<div
								class=" h-fit py-1 px-2 flex items-center justify-center rounded-sm border border-black/10 capitalize text-gray-600 dark:border-white/10 dark:text-gray-300"
							>
								TAB
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</Modal>

<style>
	input::-webkit-outer-spin-button,
	input::-webkit-inner-spin-button {
		/* display: none; <- Crashes Chrome on hover */
		-webkit-appearance: none;
		margin: 0; /* <-- Apparently some margin are still there even though it's hidden */
	}

	.tabs::-webkit-scrollbar {
		display: none; /* for Chrome, Safari and Opera */
	}

	.tabs {
		-ms-overflow-style: none; /* IE and Edge */
		scrollbar-width: none; /* Firefox */
	}

	input[type='number'] {
		-moz-appearance: textfield; /* Firefox */
	}
</style>
