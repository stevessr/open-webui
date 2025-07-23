<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import XMark from '../icons/XMark.svelte';
	import Minus from '../icons/Minus.svelte';
	import Pencil from '../icons/Pencil.svelte';
	import Check from '../icons/Check.svelte';
	import type { DocInfo } from '$lib/types';
	import { docs as docsStore } from '$lib/stores/docs';

	const dispatch = createEventDispatcher();

	// Component API
	export let show = false;

	// Data is now fully managed by the docsStore

	// Internal State
	let isMinimized = false;
	let isUrlOutOfSync = false;
	let isEditingUrl = false;

	// Element Bindings
	let containerElement: HTMLDivElement;
	let headerElement: HTMLDivElement;
	let menuElement: HTMLDivElement;
	let menuHeight = 0;

	// Reactive derived state
	$: activeDoc = $docsStore;
	let currentUrlInput = '';

	$: if (activeDoc) {
		if (activeDoc.url !== currentUrlInput && !isUrlOutOfSync) {
			currentUrlInput = activeDoc.url;
		}
	}

	// Dragging state
	let isDragging = false;
	let dragOffset = { x: 0, y: 0 };
	let position = { x: 0, y: 0 };

	// Minimized tray dragging state
	let isMinimizedDragging = false;
	let minimizedDragOffset = { x: 0, y: 0 };
	let minimizedPosition = { x: 0, y: 0 };

	// Accordion menu state
	let isMenuOpen = false;

	// State preservation for minimized iframe
	let savedIframeState = {
		url: '',
		scrollPosition: { x: 0, y: 0 },
		title: ''
	};

	// Event Handlers
	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			if (isMenuOpen) {
				isMenuOpen = false;
			} else {
				show = false;
			}
		}
	};

	const handleIframeLoad = (event: Event, doc: DocInfo) => {
		const iframe = event.currentTarget as HTMLIFrameElement;
		if (iframe && iframe.contentWindow && doc) {
			try {
				const newUrl = iframe.contentWindow.location.href;
				if (doc.url !== newUrl) {
					docsStore.updateDoc({ url: newUrl });
				}
			} catch (error) {
				console.warn('Could not access iframe location due to cross-origin restrictions', error);
				isUrlOutOfSync = true;
			}
		}

		if (doc) {
			docsStore.updateDoc({ isLoading: false });
		}
	};

	const handleReload = () => {
		if (activeDoc) {
			const iframe = document.querySelector<HTMLIFrameElement>(`#doc-iframe`);
			if (iframe && activeDoc.url) {
				docsStore.updateDoc({ isLoading: true });
				// Trigger a reload by changing the src. Using about:blank is a common way to clear it first.
				iframe.src = 'about:blank';
				setTimeout(() => {
					if (activeDoc) {
						iframe.src = activeDoc.url;
					}
				}, 100);
			}
		}
	};

	const saveIframeState = () => {
		if (activeDoc) {
			const iframe = document.querySelector<HTMLIFrameElement>(`#doc-iframe`);
			if (iframe && iframe.contentWindow) {
				try {
					savedIframeState = {
						url: activeDoc.url,
						scrollPosition: {
							x: iframe.contentWindow.scrollX || 0,
							y: iframe.contentWindow.scrollY || 0
						},
						title: activeDoc.title
					};
				} catch (error) {
					console.warn(
						'Could not save iframe scroll position due to cross-origin restrictions',
						error
					);
					savedIframeState = {
						url: activeDoc.url,
						scrollPosition: { x: 0, y: 0 },
						title: activeDoc.title
					};
				}
			}
		}
	};

	const restoreIframeState = () => {
		if (activeDoc) {
			const iframe = document.querySelector<HTMLIFrameElement>(`#doc-iframe`);
			if (iframe && savedIframeState.url && iframe.contentWindow) {
				try {
					const restoreScroll = () => {
						try {
							if (
								iframe.contentWindow &&
								(savedIframeState.scrollPosition.x !== 0 || savedIframeState.scrollPosition.y !== 0)
							) {
								iframe.contentWindow.scrollTo(
									savedIframeState.scrollPosition.x,
									savedIframeState.scrollPosition.y
								);
							}
						} catch (error) {
							console.warn(
								'Could not restore iframe scroll position due to cross-origin restrictions'
							);
						}
					};

					const handleLoad = () => {
						setTimeout(restoreScroll, 100);
						iframe.removeEventListener('load', handleLoad);
					};
					iframe.addEventListener('load', handleLoad);
				} catch (error) {
					console.warn('Could not restore iframe state due to cross-origin restrictions');
				}
			}
		}
	};

	const minimizePreview = () => {
		saveIframeState();
		isMinimized = true;
		if (minimizedPosition.x === 0 && minimizedPosition.y === 0) {
			minimizedPosition = { x: 0, y: 0 };
		}
	};

	const restorePreview = () => {
		isMinimized = false;
		setTimeout(restoreIframeState, 100);
	};

	const handleUrlSubmit = () => {
		if (activeDoc && currentUrlInput.trim() && currentUrlInput.trim() !== activeDoc.url) {
			const newUrl = currentUrlInput.trim();
			isUrlOutOfSync = false;
			docsStore.updateDoc({ url: newUrl, title: newUrl });
		}
		isEditingUrl = false;
	};

	const startEditingUrl = () => {
		if (activeDoc) {
			currentUrlInput = activeDoc.url;
			isEditingUrl = true;
		}
	};

	const cancelEditingUrl = () => {
		if (activeDoc) {
			currentUrlInput = activeDoc.url;
			isEditingUrl = false;
		}
	};

	const handleUrlKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Enter') {
			handleUrlSubmit();
			(event.target as HTMLInputElement).blur();
		} else if (event.key === 'Escape') {
			cancelEditingUrl();
			(event.target as HTMLInputElement).blur();
		}
	};

	const copyCurrentUrl = () => {
		if (activeDoc?.url) {
			navigator.clipboard.writeText(activeDoc.url);
		}
	};

	const openInNewWindow = () => {
		if (activeDoc?.url) {
			window.open(activeDoc.url, '_blank', 'noopener,noreferrer');
		}
	};

	const printPage = () => {
		if (activeDoc) {
			const iframe = document.querySelector<HTMLIFrameElement>(`#doc-iframe`);
			if (iframe && iframe.contentWindow) {
				try {
					iframe.contentWindow.print();
				} catch (error) {
					if (activeDoc?.url) {
						const printWindow = window.open(activeDoc.url, '_blank');
						printWindow?.addEventListener('load', () => printWindow?.print());
					}
				}
			}
		}
	};

	const handleMouseDown = (event: MouseEvent) => {
		if ((event.target as HTMLElement).closest('.header-controls')) {
			return;
		}
		isDragging = true;
		dragOffset = { x: event.clientX - position.x, y: event.clientY - position.y };
		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('mouseup', handleMouseUp);
		event.preventDefault();
	};

	const handleMouseMove = (event: MouseEvent) => {
		if (isDragging) {
			position = { x: event.clientX - dragOffset.x, y: event.clientY - dragOffset.y };
		}
	};

	const handleMouseUp = () => {
		isDragging = false;
		document.removeEventListener('mousemove', handleMouseMove);
		document.removeEventListener('mouseup', handleMouseUp);
	};

	const handleMinimizedMouseDown = (event: MouseEvent) => {
		if ((event.target as HTMLElement).closest('button')) return;
		isMinimizedDragging = true;
		const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		minimizedDragOffset = { x: event.clientX - rect.left, y: event.clientY - rect.top };
		document.addEventListener('mousemove', handleMinimizedMouseMove);
		document.addEventListener('mouseup', handleMinimizedMouseUp);
		event.preventDefault();
		event.stopPropagation();
	};

	const handleMinimizedMouseMove = (event: MouseEvent) => {
		if (isMinimizedDragging) {
			minimizedPosition = {
				x: event.clientX - minimizedDragOffset.x,
				y: event.clientY - minimizedDragOffset.y
			};
		}
	};

	const handleMinimizedMouseUp = () => {
		if (isMinimizedDragging) {
			const windowWidth = window.innerWidth,
				windowHeight = window.innerHeight;
			const trayWidth = 250,
				trayHeight = 60;
			const snapThreshold = 50;
			let newX = minimizedPosition.x,
				newY = minimizedPosition.y;

			if (newX < snapThreshold) newX = 16;
			else if (newX + trayWidth > windowWidth - snapThreshold)
				newX = windowWidth - trayWidth - 16;
			if (newY < snapThreshold) newY = 16;
			else if (newY + trayHeight > windowHeight - snapThreshold)
				newY = windowHeight - trayHeight - 16;

			minimizedPosition = { x: newX, y: newY };
		}
		isMinimizedDragging = false;
		document.removeEventListener('mousemove', handleMinimizedMouseMove);
		document.removeEventListener('mouseup', handleMinimizedMouseUp);
	};

	onMount(() => {
		if (show) document.addEventListener('keydown', handleKeyDown);
	});

	onDestroy(() => {
		document.removeEventListener('keydown', handleKeyDown);
		if (isDragging) handleMouseUp();
		if (isMinimizedDragging) handleMinimizedMouseUp();
	});

	let previousShow = false;
	$: if (show !== previousShow) {
		if (show) {
			document.addEventListener('keydown', handleKeyDown);
			if (!previousShow) {
				position = { x: 0, y: 0 }; // Reset position on first show
			}
			dispatch('open');
		} else {
			document.removeEventListener('keydown', handleKeyDown);
			if (isDragging) handleMouseUp();
			if (isMinimizedDragging) handleMinimizedMouseUp();
			dispatch('close');
		}
		previousShow = show;
	}

	let previousUrl = '';
	$: if (activeDoc?.url && activeDoc.url !== previousUrl) {
		// isLoading is now managed by the store, so we just track the URL change
		previousUrl = activeDoc.url;
	}

	$: if (isMenuOpen && menuElement) {
		menuHeight = menuElement.offsetHeight;
	} else {
		menuHeight = 0;
	}
</script>

{#if show}
	{#if isMinimized}
		<!-- Minimized Tray -->
		<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
		<div
			class="fixed z-[9998] bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-3 cursor-move hover:bg-white/90 dark:hover:bg-gray-900/90 transition-all duration-200"
			style="transform: translate({minimizedPosition.x || 0}px, {minimizedPosition.y || 0}px); {minimizedPosition.x ===
			0 && minimizedPosition.y === 0
				? 'bottom: 1rem; right: 1rem;'
				: ''}"
			on:mousedown={handleMinimizedMouseDown}
			transition:fly={{ x: 100, duration: 300, easing: quintOut }}
			aria-label="Draggable minimized preview"
		>
			<div class="flex items-center gap-2">
				<div
					class="w-8 h-6 bg-gray-200/70 dark:bg-gray-700/70 rounded border border-gray-300/50 dark:border-gray-600/50"
				></div>
				<div class="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">
					{activeDoc?.title ?? 'Documentation'}
				</div>

				<button
					on:click={restorePreview}
					class="p-1 rounded hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
					aria-label="Restore preview"
					title="Restore preview"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 20 20"
						fill="currentColor"
						class="size-3 text-gray-600 dark:text-gray-400"
					>
						<path
							d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5v-13A1.5 1.5 0 0015.5 2h-11zM4 3.5a.5.5 0 01.5-.5h11a.5.5 0 01.5.5v13a.5.5 0 01-.5.5h-11a.5.5 0 01-.5-.5v-13z"
						></path>
					</svg>
				</button>
				<button
					on:click={(e) => {
						e.stopPropagation();
						show = false;
					}}
					class="p-1 rounded hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
					aria-label="Close preview"
				>
					<XMark className="size-3 text-gray-600 dark:text-gray-400" />
				</button>
			</div>
		</div>
	{:else}
		<!-- Full Preview -->
		<div
			class="fixed inset-0 z-[9998] flex items-center justify-center p-4 pointer-events-none"
			transition:fade={{ duration: 200 }}
		>
			<!-- Preview Container -->
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div
				bind:this={containerElement}
				class="relative w-full max-w-6xl h-[80vh] bg-white dark:bg-gray-900 rounded-xl shadow-2xl overflow-hidden pointer-events-auto flex flex-col"
				style="transform: translate({position.x}px, {position.y}px)"
				transition:fly={{ y: 20, duration: 300, easing: quintOut }}
				role="dialog"
				aria-label="Draggable documentation preview"
				tabindex="-1"
				on:mousedown={(e) => e.stopPropagation()}
			>
				<!-- Header -->
				<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
				<div
					bind:this={headerElement}
					class="flex items-center justify-between p-3 border-b border-gray-200/80 dark:border-gray-700/60 bg-gray-50/80 dark:bg-gray-800/80 cursor-move backdrop-blur-sm flex-shrink-0"
					on:mousedown={handleMouseDown}
				>
					<div class="flex flex-col items-center gap-0.5 flex-1 min-w-0">
						<div class="font-semibold text-gray-800 dark:text-gray-100 truncate text-base">
							{activeDoc?.title ?? 'Documentation'}
						</div>

						<!-- Address Bar -->
						<div class="flex items-center gap-1.5 text-xs w-full">
							{#if isEditingUrl}
								<!-- Edit Mode -->
								<div class="relative flex-1" on:mousedown={(e) => e.stopPropagation()}>
									<input
										type="text"
										bind:value={currentUrlInput}
										on:keydown={handleUrlKeyDown}
										class="w-full px-1.5 py-0.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
										placeholder="Enter URL"
										disabled={!activeDoc}
										title="Press Enter to confirm, Esc to cancel"
										autofocus
									/>
								</div>
								<button
									on:click={handleUrlSubmit}
									class="p-1 rounded hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
									title="Confirm"
								>
									<Check className="size-3.5 text-green-600 dark:text-green-500" />
								</button>
								<button
									on:click={cancelEditingUrl}
									class="p-1 rounded hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
									title="Cancel"
								>
									<XMark className="size-3.5 text-red-600 dark:text-red-500" />
								</button>
							{:else}
								<!-- Read-only Mode -->
								<div
									class="flex-1 truncate text-gray-500 dark:text-gray-400"
									title={activeDoc?.url ?? ''}
								>
									{activeDoc?.url ?? 'No URL'}
								</div>
								<button
									on:click={startEditingUrl}
									class="p-1 rounded hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
									title="Edit URL"
									disabled={!activeDoc}
								>
									<Pencil className="size-3.5 text-gray-600 dark:text-gray-400" />
								</button>
								{#if activeDoc?.url}
									<a
										href={activeDoc.url}
										target="_blank"
										rel="noopener noreferrer"
										class="p-1 text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0"
										title="Open in new tab"
									>
										<svg
											xmlns="http://www.w3.org/2000/svg"
											viewBox="0 0 20 20"
											fill="currentColor"
											class="size-3.5"
										>
											<path
												d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"
											/>
											<path
												d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"
											/>
										</svg>
									</a>
								{/if}
							{/if}
						</div>
					</div>

					<div class="header-controls flex items-center gap-1.5 flex-shrink-0 ml-2">
						<button
							on:click={handleReload}
							class="p-1.5 rounded-md hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
							aria-label="Reload page"
							title="Reload page"
							disabled={!activeDoc || activeDoc.isLoading}
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
								class="size-4 text-gray-600 dark:text-gray-300"
							>
								<path
									fill-rule="evenodd"
									d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm-3.068-9.93a7 7 0 00-11.712 3.138.75.75 0 101.449.39 5.5 5.5 0 019.201-2.466l.312.311h-2.433a.75.75 0 000 1.5h4.243a.75.75 0 00.75-.75V3.375a.75.75 0 00-1.5 0v2.43l-.31-.31z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>

						<!-- Actions Menu Button -->
						<button
							on:click={() => (isMenuOpen = !isMenuOpen)}
							class="p-1.5 rounded-md hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
							class:active-menu={isMenuOpen}
							aria-label="Menu"
							title="Menu"
							disabled={!activeDoc}
						>
							<svg
								class="size-4 text-gray-600 dark:text-gray-300"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
								></path>
							</svg>
						</button>

						<button
							on:click={minimizePreview}
							class="p-1.5 rounded-md hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
							aria-label="Minimize preview"
							title="Minimize preview"
						>
							<Minus className="size-4 text-gray-600 dark:text-gray-300" />
						</button>
						<button
							on:click={() => (show = false)}
							class="p-1.5 rounded-md hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
							aria-label="Close preview"
							title="Close preview"
						>
							<XMark className="size-4 text-gray-600 dark:text-gray-300" />
						</button>
					</div>
				</div>

				<!-- Accordion Menu -->
				{#if isMenuOpen}
					<div
						bind:this={menuElement}
						class="flex-shrink-0 bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur-sm border-b border-gray-200/80 dark:border-gray-700/60 py-1.5"
						transition:slide={{ duration: 300, easing: quintOut }}
					>
						<button
							on:click={() => {
								copyCurrentUrl();
								isMenuOpen = false;
							}}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
						>
							Copy URL
						</button>
						<button
							on:click={() => {
								openInNewWindow();
								isMenuOpen = false;
							}}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
						>
							Open in New Window
						</button>
						<button
							on:click={() => {
								printPage();
								isMenuOpen = false;
							}}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
						>
							Print Page
						</button>
					</div>
				{/if}

				<div class="flex-grow relative z-0 overflow-y-auto">
					<!-- Loading indicator -->
					{#if activeDoc?.isLoading}
						<div
							class="absolute inset-0 flex items-center justify-center bg-white dark:bg-gray-900 z-[1]"
						>
							<div class="flex flex-col items-center gap-3">
								<div class="breathing-light rounded-full h-8 w-8"></div>
								<div class="text-sm text-gray-600 dark:text-gray-400">
									Loading documentation...
								</div>
							</div>
						</div>
					{/if}

					<!-- Empty State -->
					{#if !activeDoc}
						<div class="w-full h-full flex items-center justify-center">
							<div class="text-gray-500 dark:text-gray-400">No open document.</div>
						</div>
					{:else if activeDoc.content}
						<!-- Markdown Content -->
						<div class="prose dark:prose-invert max-w-none p-4 overflow-y-auto">
							{@html activeDoc.content}
						</div>
					{:else}
						<!-- Iframe Container -->
						<div
							class="iframe-container"
							style:margin-top="{isMenuOpen ? menuHeight : 0}px"
						>
							<iframe
								id="doc-iframe"
								src={activeDoc.url}
								title={activeDoc.title}
								class="w-full h-full border-0"
								on:load={(e) => handleIframeLoad(e, activeDoc)}
								loading="lazy"
								allowfullscreen
								sandbox="allow-same-origin allow-scripts allow-forms allow-popups allow-modals allow-downloads allow-presentation allow-pointer-lock allow-top-navigation allow-storage-access-by-user-activation allow-clipboard-write allow-web-share allow-orientation-lock allow-screen-wake-lock allow-downloads-without-user-activation allow-payment allow-encrypted-media allow-autoplay"
								referrerpolicy="no-referrer"
							></iframe>
						</div>
					{/if}
				</div>
			</div>
		</div>
	{/if}
{/if}

<style>
	/* Adjust iframe height based on whether tabs are visible */
	.flex-grow iframe {
		height: 100%;
	}

	.new-tab-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: #6b7280;
		background-color: #f9fafb;
		padding: 2rem;
		text-align: center;
	}
	:global(.dark) .new-tab-placeholder {
		color: #9ca3af;
		background-color: #1f2937;
	}
	.new-tab-placeholder h1 {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}
	:global(.dark) .new-tab-placeholder h1 {
		color: #f3f4f6;
	}
	.new-tab-placeholder p {
		font-size: 1rem;
		max-width: 400px;
	}

	.breathing-light {
		animation: breathe 2s ease-in-out infinite;
		background: linear-gradient(45deg, #3b82f6, #8b5cf6, #06b6d4, #10b981);
		background-size: 400% 400%;
	}

	@keyframes breathe {
		0% {
			opacity: 0.4;
			transform: scale(0.8);
			background-position: 0% 50%;
		}
		25% {
			opacity: 0.7;
			transform: scale(1);
			background-position: 100% 50%;
		}
		50% {
			opacity: 1;
			transform: scale(1.2);
			background-position: 50% 100%;
		}
		75% {
			opacity: 0.7;
			transform: scale(1);
			background-position: 0% 100%;
		}
		100% {
			opacity: 0.4;
			transform: scale(0.8);
			background-position: 0% 50%;
		}
	}

	.iframe-container {
		height: 100%;
		transition: margin-top 0.3s ease;
	}

	.active-menu {
		background-color: #d1d5db;
	}
	:global(.dark) .active-menu {
		background-color: #4b5563;
	}
</style>
