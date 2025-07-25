<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { tick, getContext, onMount, onDestroy } from 'svelte';
	import { config, settings } from '$lib/stores';
	import { blobToFile, calculateSHA256, extractCurlyBraceWords } from '$lib/utils';

	import { transcribeAudio } from '$lib/apis/audio';
	import XMark from '$lib/components/icons/XMark.svelte';

	import dayjs from 'dayjs';
	import LocalizedFormat from 'dayjs/plugin/localizedFormat';
	dayjs.extend(LocalizedFormat);

	const i18n = getContext('i18n');

	export let recording = false;
	export let transcribe = true;
	export let displayMedia = false;

	export let echoCancellation = true;
	export let noiseSuppression = true;
	export let autoGainControl = true;

	export let className = ' p-2.5 w-full max-w-full';

	export let onCancel = () => {};
	export let onConfirm = (data) => {};

	let loading = false;
	let confirmed = false;

	let durationSeconds = 0;
	let durationCounter = null;

	let transcription = '';

	const startDurationCounter = () => {
		durationCounter = setInterval(() => {
			durationSeconds++;
		}, 1000);
	};

	const stopDurationCounter = () => {
		clearInterval(durationCounter);
		durationSeconds = 0;
	};

	$: if (recording) {
		startRecording();
	} else {
		stopRecording();
	}

	const formatSeconds = (seconds) => {
		const minutes = Math.floor(seconds / 60);
		const remainingSeconds = seconds % 60;
		const formattedSeconds = remainingSeconds < 10 ? `0${remainingSeconds}` : remainingSeconds;
		return `${minutes}:${formattedSeconds}`;
	};

	let stream;
	let speechRecognition;

	let mediaRecorder;
	let audioChunks = [];

	const MIN_DECIBELS = -45;
	let VISUALIZER_BUFFER_LENGTH = 300;

	let visualizerData = Array(VISUALIZER_BUFFER_LENGTH).fill(0);

	// Function to calculate the RMS level from time domain data
	const calculateRMS = (data: Uint8Array) => {
		let sumSquares = 0;
		for (let i = 0; i < data.length; i++) {
			const normalizedValue = (data[i] - 128) / 128; // Normalize the data
			sumSquares += normalizedValue * normalizedValue;
		}
		return Math.sqrt(sumSquares / data.length);
	};

	const normalizeRMS = (rms) => {
		rms = rms * 10;
		const exp = 1.5; // Adjust exponent value; values greater than 1 expand larger numbers more and compress smaller numbers more
		const scaledRMS = Math.pow(rms, exp);

		// Scale between 0.01 (1%) and 1.0 (100%)
		return Math.min(1.0, Math.max(0.01, scaledRMS));
	};

	const analyseAudio = (stream) => {
		const audioContext = new AudioContext();
		const audioStreamSource = audioContext.createMediaStreamSource(stream);

		const analyser = audioContext.createAnalyser();
		analyser.minDecibels = MIN_DECIBELS;
		audioStreamSource.connect(analyser);

		const bufferLength = analyser.frequencyBinCount;

		const domainData = new Uint8Array(bufferLength);
		const timeDomainData = new Uint8Array(analyser.fftSize);

		let lastSoundTime = Date.now();

		const detectSound = () => {
			const processFrame = () => {
				if (!recording || loading) return;

				if (recording && !loading) {
					analyser.getByteTimeDomainData(timeDomainData);
					analyser.getByteFrequencyData(domainData);

					// Calculate RMS level from time domain data
					const rmsLevel = calculateRMS(timeDomainData);
					// Push the calculated decibel level to visualizerData
					visualizerData.push(normalizeRMS(rmsLevel));

					// Ensure visualizerData array stays within the buffer length
					if (visualizerData.length >= VISUALIZER_BUFFER_LENGTH) {
						visualizerData.shift();
					}

					visualizerData = visualizerData;

					// if (domainData.some((value) => value > 0)) {
					// 	lastSoundTime = Date.now();
					// }

					// if (recording && Date.now() - lastSoundTime > 3000) {
					// 	if ($settings?.speechAutoSend ?? false) {
					// 		confirmRecording();
					// 	}
					// }
				}

				window.requestAnimationFrame(processFrame);
			};

			window.requestAnimationFrame(processFrame);
		};

		detectSound();
	};

	const onStopHandler = async (audioBlob, ext: string = 'wav') => {
		// Create a blob from the audio chunks

		await tick();
		const file = blobToFile(audioBlob, `Recording-${dayjs().format('L LT')}.${ext}`);

		if (transcribe) {
			if ($config.audio.stt.engine === 'web' || ($settings?.audio?.stt?.engine ?? '') === 'web') {
				// with web stt, we don't need to send the file to the server
				return;
			}

			const res = await transcribeAudio(
				localStorage.token,
				file,
				$settings?.audio?.stt?.language
			).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				console.log(res);
				onConfirm(res);
			}
		} else {
			onConfirm({
				file: file,
				blob: audioBlob
			});
		}
	};

	const startRecording = async () => {
		loading = true;

		try {
			if (displayMedia) {
				const mediaStream = await navigator.mediaDevices.getDisplayMedia({
					audio: true
				});

				stream = new MediaStream();
				for (const track of mediaStream.getAudioTracks()) {
					stream.addTrack(track);
				}

				for (const track of mediaStream.getVideoTracks()) {
					track.stop();
				}
			} else {
				stream = await navigator.mediaDevices.getUserMedia({
					audio: {
						echoCancellation: echoCancellation,
						noiseSuppression: noiseSuppression,
						autoGainControl: autoGainControl
					}
				});
			}
		} catch (err) {
			console.error('Error accessing media devices.', err);
			toast.error($i18n.t('Error accessing media devices.'));
			loading = false;
			recording = false;
			return;
		}

		const mineTypes = ['audio/webm; codecs=opus', 'audio/mp4'];

		mediaRecorder = new MediaRecorder(stream, {
			mimeType: mineTypes.find((type) => MediaRecorder.isTypeSupported(type))
		});

		mediaRecorder.onstart = () => {
			console.log('Recording started');
			loading = false;
			startDurationCounter();

			audioChunks = [];
			analyseAudio(stream);
		};
		mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
		mediaRecorder.onstop = async () => {
			console.log('Recording stopped');

			if (confirmed) {
				// Use the actual type provided by MediaRecorder
				let type = audioChunks[0]?.type || mediaRecorder.mimeType || 'audio/webm';

				// split `/` and `;` to get the extension
				let ext = type.split('/')[1].split(';')[0] || 'webm';

				// If not audio, default to audio/webm
				if (!type.startsWith('audio/')) {
					ext = 'webm';
				}

				const audioBlob = new Blob(audioChunks, { type: type });
				await onStopHandler(audioBlob, ext);

				confirmed = false;
				loading = false;
			}

			audioChunks = [];
			recording = false;
		};

		try {
			mediaRecorder.start();
		} catch (error) {
			console.error('Error starting recording:', error);
			toast.error($i18n.t('Error starting recording.'));
			loading = false;
			recording = false;
			return;
		}

		if (transcribe) {
			if ($config.audio.stt.engine === 'web' || ($settings?.audio?.stt?.engine ?? '') === 'web') {
				if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
					// Create a SpeechRecognition object
					speechRecognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

					// Set continuous to true for continuous recognition
					speechRecognition.continuous = true;

					// Set the timeout for turning off the recognition after inactivity (in milliseconds)
					const inactivityTimeout = 2000; // 3 seconds

					let timeoutId;
					// Start recognition
					speechRecognition.start();

					// Event triggered when speech is recognized
					speechRecognition.onresult = async (event) => {
						// Clear the inactivity timeout
						clearTimeout(timeoutId);

						// Handle recognized speech
						console.log(event);
						const transcript = event.results[Object.keys(event.results).length - 1][0].transcript;

						transcription = `${transcription}${transcript}`;

						await tick();
						document.getElementById('chat-input')?.focus();

						// Restart the inactivity timeout
						timeoutId = setTimeout(() => {
							console.log('Speech recognition turned off due to inactivity.');
							speechRecognition.stop();
						}, inactivityTimeout);
					};

					// Event triggered when recognition is ended
					speechRecognition.onend = function () {
						// Restart recognition after it ends
						console.log('recognition ended');

						confirmRecording();
						onConfirm({
							text: transcription
						});
						confirmed = false;
						loading = false;
					};

					// Event triggered when an error occurs
					speechRecognition.onerror = function (event) {
						console.log(event);
						toast.error($i18n.t(`Speech recognition error: {{error}}`, { error: event.error }));
						onCancel();

						stopRecording();
					};
				}
			}
		}
	};

	const stopRecording = async () => {
		if (recording && mediaRecorder) {
			await mediaRecorder.stop();
		}

		if (speechRecognition) {
			speechRecognition.stop();
		}

		stopDurationCounter();
		audioChunks = [];

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	const confirmRecording = async () => {
		loading = true;
		confirmed = true;

		if (recording && mediaRecorder) {
			await mediaRecorder.stop();
		}
		clearInterval(durationCounter);

		if (stream) {
			const tracks = stream.getTracks();
			tracks.forEach((track) => track.stop());
		}

		stream = null;
	};

	let resizeObserver;
	let containerWidth;

	let maxVisibleItems = 300;
	$: maxVisibleItems = Math.floor(containerWidth / 5); // 2px width + 0.5px gap

	onMount(() => {
		// listen to width changes
		resizeObserver = new ResizeObserver(() => {
			VISUALIZER_BUFFER_LENGTH = Math.floor(window.innerWidth / 4);
			if (visualizerData.length > VISUALIZER_BUFFER_LENGTH) {
				visualizerData = visualizerData.slice(visualizerData.length - VISUALIZER_BUFFER_LENGTH);
			} else {
				visualizerData = Array(VISUALIZER_BUFFER_LENGTH - visualizerData.length)
					.fill(0)
					.concat(visualizerData);
			}
		});

		resizeObserver.observe(document.body);
	});

	onDestroy(() => {
		// remove resize observer
		resizeObserver.disconnect();
	});
</script>

<div
	bind:clientWidth={containerWidth}
	class="{loading
		? ' bg-gray-100/50 dark:bg-gray-850/50'
		: 'bg-indigo-300/10 dark:bg-indigo-500/10 '} rounded-full flex justify-between {className}"
>
	<div class="flex items-center mr-1">
		<button
			type="button"
			class="p-1.5

            {loading
				? ' bg-gray-200 dark:bg-gray-700/50'
				: 'bg-indigo-400/20 text-indigo-600 dark:text-indigo-300 '} 


             rounded-full"
			on:click={async () => {
				stopRecording();
				onCancel();
			}}
		>
			<XMark className={'size-4'} />
		</button>
	</div>

	<div
		class="flex flex-1 self-center items-center justify-between ml-2 mx-1 overflow-hidden h-6"
		dir="rtl"
	>
		<div
			class="flex items-center gap-0.5 h-6 w-full max-w-full overflow-hidden overflow-x-hidden flex-wrap"
		>
			{#each visualizerData.slice().reverse() as rms}
				<div class="flex items-center h-full">
					<div
						class="w-[2px] shrink-0
                    
                    {loading
							? ' bg-gray-500 dark:bg-gray-400   '
							: 'bg-indigo-500 dark:bg-indigo-400  '} 
                    
                    inline-block h-full"
						style="height: {Math.min(100, Math.max(14, rms * 100))}%;"
					/>
				</div>
			{/each}
		</div>
	</div>

	<div class="flex">
		<div class="  mx-1.5 pr-1 flex justify-center items-center">
			<div
				class="text-sm
        
        
        {loading ? ' text-gray-500  dark:text-gray-400  ' : ' text-indigo-400 '} 
       font-medium flex-1 mx-auto text-center"
			>
				{formatSeconds(durationSeconds)}
			</div>
		</div>

		<div class="flex items-center">
			{#if loading}
				<div class="voice-breathing-light w-6 h-6 rounded-full cursor-not-allowed">
					<style>
						.voice-breathing-light {
							background: linear-gradient(45deg, #6b7280, #9ca3af, #d1d5db, #f3f4f6);
							background-size: 400% 400%;
							animation: voice-breathe 2s ease-in-out infinite;
							display: flex;
							align-items: center;
							justify-content: center;
						}

						@keyframes voice-breathe {
							0% {
								opacity: 0.4;
								transform: scale(0.9);
								background-position: 0% 50%;
								box-shadow: 0 0 5px rgba(107, 114, 128, 0.3);
							}
							25% {
								opacity: 0.7;
								transform: scale(1.0);
								background-position: 100% 50%;
								box-shadow: 0 0 10px rgba(156, 163, 175, 0.5);
							}
							50% {
								opacity: 1.0;
								transform: scale(1.1);
								background-position: 50% 100%;
								box-shadow: 0 0 15px rgba(209, 213, 219, 0.7);
							}
							75% {
								opacity: 0.7;
								transform: scale(1.0);
								background-position: 0% 100%;
								box-shadow: 0 0 10px rgba(156, 163, 175, 0.5);
							}
							100% {
								opacity: 0.4;
								transform: scale(0.9);
								background-position: 0% 50%;
								box-shadow: 0 0 5px rgba(107, 114, 128, 0.3);
							}
						}

						/* Dark mode adjustments */
						:global(.dark) .voice-breathing-light {
							background: linear-gradient(45deg, #374151, #4b5563, #6b7280, #9ca3af);
						}
					</style>
				</div>
			{:else}
				<button
					type="button"
					class="p-1.5 bg-indigo-500 text-white dark:bg-indigo-500 dark:text-blue-950 rounded-full"
					on:click={async () => {
						await confirmRecording();
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="2.5"
						stroke="currentColor"
						class="size-4"
					>
						<path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
					</svg>
				</button>
			{/if}
		</div>
	</div>
</div>

<style>
	.visualizer {
		display: flex;
		height: 100%;
	}

	.visualizer-bar {
		width: 2px;
		background-color: #4a5aba; /* or whatever color you need */
	}
</style>
