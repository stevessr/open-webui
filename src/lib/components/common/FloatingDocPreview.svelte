<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy, tick } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import XMark from '../icons/XMark.svelte';
	import Minus from '../icons/Minus.svelte';
	import type { DocInfo } from '$lib/types';
	import { docs as docsStore } from '$lib/stores/docs';

	const dispatch = createEventDispatcher();

	// Component API
	export let show = false;

	export let docs: DocInfo[] = [];
	export let activeDocId: string | null = null;

	// Internal State
	let isMinimized = false;
	let isLoading = true;

	// Element Bindings
	let iframeElement: HTMLIFrameElement;
	let containerElement: HTMLDivElement;
	let headerElement: HTMLDivElement;
	let urlInputElement: HTMLInputElement;

	// Reactive derived state
	$: activeDoc = docs.find((doc: DocInfo) => doc.id === activeDocId) || null;

	// Dragging state
	let isDragging = false;
	let dragOffset = { x: 0, y: 0 };
	let position = { x: 0, y: 0 };

	// Minimized tray dragging state
	let isMinimizedDragging = false;
	let minimizedDragOffset = { x: 0, y: 0 };
	let minimizedPosition = { x: 0, y: 0 };

	// URL editing state
	let isEditingUrl = false;
	let editableUrl = '';

	// Actions menu state
	let showActionsMenu = false;

	// State preservation for minimized iframe
	let savedIframeState = {
		url: '',
		scrollPosition: { x: 0, y: 0 },
		title: ''
	};

	// Event Handlers
	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			if (showActionsMenu) {
				showActionsMenu = false;
			} else {
				show = false;
			}
		}
	};

	const handleIframeLoad = () => {
		isLoading = false;
	};

	const handleCloseTab = (e: MouseEvent, docId: string) => {
		e.stopPropagation(); // Prevent tab selection when closing
		docsStore.closeDoc(docId);
	};

	const handleReload = () => {
		if (iframeElement && activeDoc?.url) {
			isLoading = true;
			// Force reload by setting src to empty then back to original URL
			iframeElement.src = '';
			setTimeout(() => {
				if (activeDoc) iframeElement.src = activeDoc.url;
			}, 10);
		}
	};

	// State Management for Minimizing
	const saveIframeState = () => {
		if (iframeElement && iframeElement.contentWindow && activeDoc) {
			try {
				savedIframeState = {
					url: activeDoc.url,
					scrollPosition: {
						x: iframeElement.contentWindow.scrollX || 0,
						y: iframeElement.contentWindow.scrollY || 0
					},
					title: activeDoc.title
				};
			} catch (error) {
				console.warn('Could not save iframe scroll position due to cross-origin restrictions');
				savedIframeState = {
					url: activeDoc.url,
					scrollPosition: { x: 0, y: 0 },
					title: activeDoc.title
				};
			}
		}
	};

	const restoreIframeState = () => {
		if (iframeElement && savedIframeState.url && iframeElement.contentWindow) {
			try {
				const restoreScroll = () => {
					try {
						if (
							iframeElement.contentWindow &&
							(savedIframeState.scrollPosition.x !== 0 ||
								savedIframeState.scrollPosition.y !== 0)
						) {
							iframeElement.contentWindow.scrollTo(
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
					iframeElement.removeEventListener('load', handleLoad);
				};
				iframeElement.addEventListener('load', handleLoad);
			} catch (error) {
				console.warn('Could not restore iframe state due to cross-origin restrictions');
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

	// URL editing functions (Note: This might need re-evaluation in a multi-tab context)
	const startEditingUrl = async () => {
		if (!activeDoc) return;
		isEditingUrl = true;
		editableUrl = activeDoc.url;
		await tick();
		urlInputElement?.focus();
	};

	const cancelEditingUrl = () => {
		isEditingUrl = false;
		editableUrl = '';
	};

	const saveEditedUrl = () => {
		if (editableUrl.trim() && activeDoc) {
			// In a real app, you'd probably dispatch an event to update the doc source
			// For now, we'll just reload the iframe with the new URL
			isLoading = true;
			if (iframeElement) {
				iframeElement.src = editableUrl.trim();
			}
		}
		isEditingUrl = false;
		editableUrl = '';
	};

	const handleUrlKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Enter') saveEditedUrl();
		else if (event.key === 'Escape') cancelEditingUrl();
	};

	// Bottom menu functions
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
		if (iframeElement && iframeElement.contentWindow) {
			try {
				iframeElement.contentWindow.print();
			} catch (error) {
				// Fallback
				if (activeDoc?.url) {
					const printWindow = window.open(activeDoc.url, '_blank');
					printWindow?.addEventListener('load', () => printWindow.print());
				}
			}
		}
	};

	// Drag functionality
	const handleMouseDown = (event: MouseEvent) => {
		if ((event.target as HTMLElement).closest('.tab-bar, .header-controls')) {
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

	// Minimized tray drag functionality
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

	// Lifecycle and watchers
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
		isLoading = true;
		previousUrl = activeDoc.url;
		// The iframe `src` is reactively bound, so no need to set it manually here.
	}
</script>

{#if show}
	{#if isMinimized}
		<!-- Minimized Tray -->
				<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
				<div
					class="fixed z-[9998] bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-3 cursor-move hover:bg-white/90 dark:hover:bg-gray-900/90 transition-all duration-200"
					style="transform: translate({minimizedPosition.x || 0}px, {minimizedPosition.y ||
						0}px); {minimizedPosition.x === 0 && minimizedPosition.y === 0
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
							class="flex items-center justify-between p-3 border-b border-gray-200/80 dark:border-gray-700/60 bg-gray-50/80 dark:bg-gray-800/80 cursor-move backdrop-blur-sm"
							on:mousedown={handleMouseDown}
						>
							<div class="flex flex-col items-center gap-0.5 flex-1 min-w-0">
								<div class="font-semibold text-gray-800 dark:text-gray-100 truncate text-base">
									{activeDoc?.title ?? 'Documentation'}
								</div>
		
								<!-- Editable URL field -->
								<div class="flex items-center gap-2">
									{#if isEditingUrl}
										<input
											bind:this={urlInputElement}
											type="url"
											bind:value={editableUrl}
											on:keydown={handleUrlKeyDown}
											on:blur={cancelEditingUrl}
											class="flex-1 px-1.5 py-0.5 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
											placeholder="Enter URL..."
										/>
										<button
											on:click={saveEditedUrl}
											class="px-2 py-0.5 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
											title="Save URL"
										>
											Save
										</button>
										<button
											on:click={cancelEditingUrl}
											class="px-2 py-0.5 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors"
											title="Cancel"
										>
											Cancel
										</button>
									{:else}
										<button
											on:click={startEditingUrl}
											class="flex-1 text-left text-xs text-blue-600 dark:text-blue-400 hover:underline truncate"
											title="Click to edit URL"
										>
											{activeDoc?.url ?? 'No URL'}
										</button>
										{#if activeDoc?.url}
											<a
												href={activeDoc.url}
												target="_blank"
												rel="noopener noreferrer"
												class="text-xs text-blue-600 dark:text-blue-400 hover:underline flex-shrink-0"
												title="Open in new tab"
											>
												↗
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
									disabled={!activeDoc}
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
		
								<!-- Actions Menu -->
								<div class="relative">
									<button
										on:click={() => (showActionsMenu = !showActionsMenu)}
										class="p-1.5 rounded-md hover:bg-gray-200/70 dark:hover:bg-gray-700/70 transition-colors"
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
		
									{#if showActionsMenu}
										<div
											class="absolute top-full right-0 mt-2 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200/50 dark:border-gray-700/50 py-1.5 min-w-[180px] z-20"
											transition:fly={{ y: -5, duration: 200, easing: quintOut }}
										>
											<button
												on:click={() => {
													copyCurrentUrl();
													showActionsMenu = false;
												}}
												class="w-full px-3 py-1.5 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
											>
												Copy URL
											</button>
											<button
												on:click={() => {
													openInNewWindow();
													showActionsMenu = false;
												}}
												class="w-full px-3 py-1.5 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
											>
												Open in New Window
											</button>
											<button
												on:click={() => {
													printPage();
													showActionsMenu = false;
												}}
												class="w-full px-3 py-1.5 text-left text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-200/60 dark:hover:bg-gray-700/60 transition-colors flex items-center gap-2"
											>
												Print Page
											</button>
										</div>
									{/if}
								</div>
		
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
		
						<!-- Tab Bar -->
						{#if docs.length > 0}
							<div
								class="tab-bar flex-shrink-0 flex items-end gap-1 px-3 border-b border-gray-200/80 dark:border-gray-700/60"
							>
								{#each docs as doc (doc.id)}
									<button
										class="tab"
										class:active={doc.id === activeDocId}
										on:click={() => docsStore.selectDoc(doc.id)}
									>
										<span class="truncate">{doc.title}</span>
										<button class="close-tab-btn" on:click={(e) => handleCloseTab(e, doc.id)}>
											<XMark className="size-3" />
										</button>
									</button>
								{/each}

								<button
									class="new-tab-btn"
									on:click={() => docsStore.openNewTab()}
									title="Open new tab"
								>
									+
								</button>
							</div>
						{/if}

						<div class="flex-grow relative">
							<!-- Loading indicator -->
							{#if isLoading && activeDoc}
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
							{#if docs.length === 0}
								<div class="w-full h-full flex items-center justify-center">
									<div class="text-gray-500 dark:text-gray-400">No open documents.</div>
								</div>
							{:else if activeDoc}
								<!-- Iframe -->
								<iframe
									bind:this={iframeElement}
									src={activeDoc.url}
									title={activeDoc.title}
									class="w-full h-full border-0"
									on:load={handleIframeLoad}
									loading="lazy"
									allowfullscreen
									sandbox="allow-scripts allow-forms allow-popups allow-modals allow-downloads allow-presentation allow-same-origin"
									referrerpolicy="no-referrer"
								></iframe>
							{/if}
						</div>
					</div>
				</div>
			{/if}
{/if}

<style>
	.tab-bar {
		background-color: rgba(243, 244, 246, 0.8); /* gray-100/80 */
	}
	:global(.dark) .tab-bar {
		background-color: rgba(31, 41, 55, 0.8); /* gray-800/80 */
	}

	.tab {
		position: relative;
		display: flex;
		align-items: center;
		gap: theme('spacing.2');
		padding: theme('spacing.2') theme('spacing.4');
		border: 1px solid transparent;
		border-bottom: none;
		border-radius: 6px 6px 0 0;
		font-size: theme('fontSize.sm');
		max-width: 200px;
		color: theme('colors.gray.500');
		background-color: transparent;
		transition:
			background-color 0.2s,
			color 0.2s;
	}
	:global(.dark) .tab {
		color: theme('colors.gray.400');
	}

	.tab:hover {
		background-color: rgba(229, 231, 235, 0.6); /* gray-200/60 */
		color: theme('colors.gray.700');
	}
	:global(.dark) .tab:hover {
		background-color: rgba(55, 65, 81, 0.6); /* gray-700/60 */
		color: theme('colors.gray.200');
	}

	.tab.active {
		background-color: theme('colors.white');
		color: theme('colors.gray.900');
		border-color: rgba(229, 231, 235, 1); /* gray-200 */
		border-bottom: 1px solid theme('colors.white');
		z-index: 1;
		margin-bottom: -1px; /* Overlap the bottom border of the tab bar */
	}

	:global(.dark) .tab.active {
		background-color: theme('colors.gray.900');
		color: theme('colors.white');
		border-color: rgba(75, 85, 99, 1); /* gray-600 */
		border-bottom: 1px solid theme('colors.gray.900');
	}

	.new-tab-btn {
		padding: theme('spacing.1') theme('spacing.2');
		margin-left: theme('spacing.1');
		margin-bottom: 4px; /* Align with tab bottom edge */
		border-radius: 6px;
		font-size: theme('fontSize.lg');
		line-height: 1;
		color: theme('colors.gray.500');
		transition: all 0.2s;
	}
	:global(.dark) .new-tab-btn {
		color: theme('colors.gray.400');
	}

	.new-tab-btn:hover {
		background-color: rgba(229, 231, 235, 0.6); /* gray-200/60 */
		color: theme('colors.gray.700');
	}
	:global(.dark) .new-tab-btn:hover {
		background-color: rgba(55, 65, 81, 0.6); /* gray-700/60 */
		color: theme('colors.gray.200');
	}

	.close-tab-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2px;
		border-radius: 9999px;
		color: theme('colors.gray.500');
		transition:
			background-color 0.2s,
			color 0.2s;
	}
	.tab:hover .close-tab-btn {
		color: theme('colors.gray.700');
	}
	:global(.dark) .tab:hover .close-tab-btn {
		color: theme('colors.gray.200');
	}
	.close-tab-btn:hover {
		background-color: rgba(209, 213, 219, 1); /* gray-300 */
	}
	:global(.dark) .close-tab-btn:hover {
		background-color: rgba(75, 85, 99, 1); /* gray-600 */
	}
	.tab.active .close-tab-btn {
		color: theme('colors.gray.600');
	}
	:global(.dark) .tab.active .close-tab-btn {
		color: theme('colors.gray.300');
	}

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
		color: theme('colors.gray.500');
		background-color: theme('colors.gray.50');
		padding: theme('spacing.8');
		text-align: center;
	}
	:global(.dark) .new-tab-placeholder {
		color: theme('colors.gray.400');
		background-color: theme('colors.gray.800');
	}
	.new-tab-placeholder h1 {
		font-size: theme('fontSize.2xl');
		font-weight: theme('fontWeight.bold');
		color: theme('colors.gray.800');
		margin-bottom: theme('spacing.2');
	}
	:global(.dark) .new-tab-placeholder h1 {
		color: theme('colors.gray.100');
	}
	.new-tab-placeholder p {
		font-size: theme('fontSize.base');
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
</style>
