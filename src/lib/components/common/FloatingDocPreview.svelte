<script lang="ts">
	import { createEventDispatcher, onMount, onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { quintOut } from 'svelte/easing';
	import XMark from '../icons/XMark.svelte';
	import ChevronLeft from '../icons/ChevronLeft.svelte';
	import ChevronRight from '../icons/ChevronRight.svelte';
	import Minus from '../icons/Minus.svelte';

	const dispatch = createEventDispatcher();

	export let show = false;
	export let url = '';
	export let title = 'Documentation';
	export let pages: Array<{url: string, title: string}> = [];

	let isMinimized = false;

	let iframeElement: HTMLIFrameElement;
	let containerElement: HTMLDivElement;
	let headerElement: HTMLDivElement;
	let isLoading = true;
	let currentPageIndex = 0;

	// Multi-page support
	$: allPages = pages.length > 0 ? pages : [{url, title}];
	$: canNavigateBack = currentPageIndex > 0;
	$: canNavigateForward = currentPageIndex < allPages.length - 1;

	// Get current page without cyclical dependency
	function getCurrentPage() {
		return allPages[currentPageIndex] || allPages[0] || {url, title};
	}

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

	// Bottom-left menu state
	let showBottomMenu = false;

	// State preservation for minimized iframe
	let savedIframeState = {
		url: '',
		scrollPosition: { x: 0, y: 0 },
		title: ''
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape') {
			if (showBottomMenu) {
				showBottomMenu = false;
			} else {
				show = false;
			}
		}
	};



	const handleIframeLoad = () => {
		isLoading = false;
	};

	const handleReload = () => {
		const currentPage = getCurrentPage();
		if (iframeElement && currentPage.url) {
			isLoading = true;
			// Force reload by setting src to empty then back to original URL
			iframeElement.src = '';
			setTimeout(() => {
				iframeElement.src = currentPage.url;
			}, 10);
		}
	};

	const navigateToPage = (index: number) => {
		if (index >= 0 && index < allPages.length) {
			currentPageIndex = index;
			isLoading = true;
		}
	};

	const navigateBack = () => {
		if (canNavigateBack) {
			navigateToPage(currentPageIndex - 1);
		}
	};

	const navigateForward = () => {
		if (canNavigateForward) {
			navigateToPage(currentPageIndex + 1);
		}
	};

	const saveIframeState = () => {
		if (iframeElement && iframeElement.contentWindow) {
			try {
				const currentPage = getCurrentPage();
				savedIframeState = {
					url: currentPage.url,
					scrollPosition: {
						x: iframeElement.contentWindow.scrollX || 0,
						y: iframeElement.contentWindow.scrollY || 0
					},
					title: currentPage.title
				};
			} catch (error) {
				// Cross-origin restrictions may prevent access to iframe content
				console.warn('Could not save iframe scroll position due to cross-origin restrictions');
				savedIframeState = {
					url: getCurrentPage().url,
					scrollPosition: { x: 0, y: 0 },
					title: getCurrentPage().title
				};
			}
		}
	};

	const restoreIframeState = () => {
		if (iframeElement && savedIframeState.url && iframeElement.contentWindow) {
			try {
				// Restore scroll position after iframe loads
				const restoreScroll = () => {
					try {
						if (savedIframeState.scrollPosition.x !== 0 || savedIframeState.scrollPosition.y !== 0) {
							iframeElement.contentWindow.scrollTo(
								savedIframeState.scrollPosition.x,
								savedIframeState.scrollPosition.y
							);
						}
					} catch (error) {
						console.warn('Could not restore iframe scroll position due to cross-origin restrictions');
					}
				};

				// Wait for iframe to load before restoring scroll position
				const handleLoad = () => {
					setTimeout(restoreScroll, 100); // Small delay to ensure content is rendered
					iframeElement.removeEventListener('load', handleLoad);
				};

				iframeElement.addEventListener('load', handleLoad);
			} catch (error) {
				console.warn('Could not restore iframe state due to cross-origin restrictions');
			}
		}
	};

	const minimizePreview = () => {
		// Save current iframe state before minimizing
		saveIframeState();
		isMinimized = true;
		// Reset minimized position to default (bottom-right) if not already positioned
		if (minimizedPosition.x === 0 && minimizedPosition.y === 0) {
			minimizedPosition = { x: 0, y: 0 }; // Will use CSS positioning for default
		}
	};

	const restorePreview = () => {
		isMinimized = false;
		// Restore iframe state after a short delay to ensure the iframe is visible
		setTimeout(() => {
			restoreIframeState();
		}, 100);
	};

	// URL editing functions
	const startEditingUrl = () => {
		isEditingUrl = true;
		editableUrl = getCurrentPage().url;
	};

	const cancelEditingUrl = () => {
		isEditingUrl = false;
		editableUrl = '';
	};

	const saveEditedUrl = () => {
		if (editableUrl.trim()) {
			// Update the current page URL
			const currentPage = getCurrentPage();
			if (pages.length > 0) {
				pages[currentPageIndex] = { ...currentPage, url: editableUrl.trim() };
			} else {
				// If no pages array, update the main url prop
				url = editableUrl.trim();
			}

			// Reload the iframe with the new URL
			isLoading = true;
			if (iframeElement) {
				iframeElement.src = editableUrl.trim();
			}
		}
		isEditingUrl = false;
		editableUrl = '';
	};

	const handleUrlKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Enter') {
			saveEditedUrl();
		} else if (event.key === 'Escape') {
			cancelEditingUrl();
		}
	};

	// Bottom menu functions
	const toggleBottomMenu = () => {
		showBottomMenu = !showBottomMenu;
	};

	const copyCurrentUrl = () => {
		const currentUrl = getCurrentPage().url;
		if (currentUrl) {
			navigator.clipboard.writeText(currentUrl).then(() => {
				// Could show a toast notification here
				console.log('URL copied to clipboard');
			}).catch(err => {
				console.error('Failed to copy URL: ', err);
			});
		}
		showBottomMenu = false;
	};

	const openInNewWindow = () => {
		const currentUrl = getCurrentPage().url;
		if (currentUrl) {
			window.open(currentUrl, '_blank', 'noopener,noreferrer');
		}
		showBottomMenu = false;
	};

	const printPage = () => {
		if (iframeElement && iframeElement.contentWindow) {
			try {
				iframeElement.contentWindow.print();
			} catch (error) {
				console.warn('Could not print iframe content due to cross-origin restrictions');
				// Fallback: open in new window and print
				const currentUrl = getCurrentPage().url;
				if (currentUrl) {
					const printWindow = window.open(currentUrl, '_blank');
					if (printWindow) {
						printWindow.onload = () => {
							printWindow.print();
						};
					}
				}
			}
		}
		showBottomMenu = false;
	};

	// Drag functionality
	const handleMouseDown = (event: MouseEvent) => {
		isDragging = true;
		// Calculate offset from mouse to current position
		dragOffset = {
			x: event.clientX - position.x,
			y: event.clientY - position.y
		};
		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('mouseup', handleMouseUp);
		event.preventDefault();
	};

	const handleMouseMove = (event: MouseEvent) => {
		if (isDragging) {
			// Update position to follow mouse, maintaining the offset
			position = {
				x: event.clientX - dragOffset.x,
				y: event.clientY - dragOffset.y
			};
		}
	};

	const handleMouseUp = () => {
		isDragging = false;
		document.removeEventListener('mousemove', handleMouseMove);
		document.removeEventListener('mouseup', handleMouseUp);
	};

	// Minimized tray drag functionality
	const handleMinimizedMouseDown = (event: MouseEvent) => {
		// Don't drag if clicking the close button
		if ((event.target as HTMLElement).closest('button')) {
			return;
		}

		isMinimizedDragging = true;
		const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
		minimizedDragOffset = {
			x: event.clientX - rect.left,
			y: event.clientY - rect.top
		};
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
			// Auto-snap to edges
			const windowWidth = window.innerWidth;
			const windowHeight = window.innerHeight;
			const trayWidth = 250; // Approximate width of minimized tray
			const trayHeight = 60; // Approximate height of minimized tray
			const snapThreshold = 50;

			let newX = minimizedPosition.x;
			let newY = minimizedPosition.y;

			// Snap to left or right edge
			if (minimizedPosition.x < snapThreshold) {
				newX = 16; // 1rem padding
			} else if (minimizedPosition.x + trayWidth > windowWidth - snapThreshold) {
				newX = windowWidth - trayWidth - 16;
			}

			// Snap to top or bottom edge
			if (minimizedPosition.y < snapThreshold) {
				newY = 16;
			} else if (minimizedPosition.y + trayHeight > windowHeight - snapThreshold) {
				newY = windowHeight - trayHeight - 16;
			}

			minimizedPosition = { x: newX, y: newY };
		}

		isMinimizedDragging = false;
		document.removeEventListener('mousemove', handleMinimizedMouseMove);
		document.removeEventListener('mouseup', handleMinimizedMouseUp);
	};

	onMount(() => {
		if (show) {
			document.addEventListener('keydown', handleKeyDown);
		}
	});

	onDestroy(() => {
		document.removeEventListener('keydown', handleKeyDown);
		// Clean up drag listeners
		if (isDragging) {
			handleMouseUp();
		}
		if (isMinimizedDragging) {
			handleMinimizedMouseUp();
		}
	});

	let previousShow = false;
	let previousUrl = '';

	$: if (show) {
		document.addEventListener('keydown', handleKeyDown);

		const currentPage = getCurrentPage();
		// Only set loading state when first opening or URL changes
		if (!previousShow || currentPage.url !== previousUrl) {
			isLoading = true;
			previousUrl = currentPage.url;
		}

		// Reset position when opening (not when dragging)
		if (!previousShow) {
			position = { x: 0, y: 0 };
			currentPageIndex = 0; // Reset to first page when opening
		}

		previousShow = true;
	} else {
		document.removeEventListener('keydown', handleKeyDown);
		// Clean up drag listeners if modal is closed while dragging
		if (isDragging) {
			handleMouseUp();
		}
		if (isMinimizedDragging) {
			handleMinimizedMouseUp();
		}
		previousShow = false;
	}

	// Handle URL changes for current page
	$: {
		const currentPage = getCurrentPage();
		if (currentPage.url && iframeElement) {
			if (currentPage.url !== previousUrl) {
				isLoading = true;
				iframeElement.src = currentPage.url;
				previousUrl = currentPage.url;
			}
		}
	}

	$: if (show) {
		dispatch('open');
	} else {
		dispatch('close');
	}
</script>

{#if show}
	{#if isMinimized}
		<!-- Minimized Tray -->
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<div
			class="fixed z-[9998] bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-lg shadow-lg border border-gray-200/50 dark:border-gray-700/50 p-3 cursor-move hover:bg-white/90 dark:hover:bg-gray-900/90 transition-all duration-200"
			style="transform: translate({minimizedPosition.x || 0}px, {minimizedPosition.y || 0}px); {minimizedPosition.x === 0 && minimizedPosition.y === 0 ? 'bottom: 1rem; right: 1rem;' : ''}"
			on:mousedown={handleMinimizedMouseDown}
			transition:fly={{ x: 100, duration: 300, easing: quintOut }}
			role="button"
			tabindex="0"
			aria-label="Draggable minimized preview - click to restore"
			on:keydown={(e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					restorePreview();
				}
			}}
			on:click={() => {
				// Only restore if not dragging
				if (!isMinimizedDragging) {
					restorePreview();
				}
			}}
		>
			<div class="flex items-center gap-2">
				<div class="w-8 h-6 bg-gray-200/70 dark:bg-gray-700/70 rounded border border-gray-300/50 dark:border-gray-600/50"></div>
				<div class="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">
					{getCurrentPage().title}
				</div>
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
			class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
			transition:fade={{ duration: 200 }}
		>
			<!-- Backdrop -->
			<div class="absolute inset-0 bg-black/20 dark:bg-black/40"></div>

			<!-- Preview Container -->
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div
				bind:this={containerElement}
				class="relative w-full max-w-6xl h-[80vh] bg-white dark:bg-gray-900 rounded-xl shadow-2xl overflow-hidden"
				style="transform: translate({position.x}px, {position.y}px)"
				transition:fly={{ y: 20, duration: 300, easing: quintOut }}
				role="dialog"
				aria-label="Draggable documentation preview"
				tabindex="-1"
				on:mousedown={(e) => e.stopPropagation()}
			>
			<!-- Header -->
			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<div
				bind:this={headerElement}
				class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 cursor-move select-none"
				on:mousedown={handleMouseDown}
			>
				<div class="flex items-center gap-3 flex-1 min-w-0">
					<!-- Navigation controls for multi-page -->
					{#if allPages.length > 1}
						<div class="flex items-center gap-1">
							<button
								on:click={navigateBack}
								disabled={!canNavigateBack}
								class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors theme-button disabled:opacity-50 disabled:cursor-not-allowed"
								aria-label="Previous page"
								title="Previous page"
							>
								<ChevronLeft className="size-4 text-gray-600 dark:text-gray-400 theme-icon" />
							</button>
							<span class="text-xs text-gray-500 dark:text-gray-400 px-2">
								{currentPageIndex + 1} / {allPages.length}
							</span>
							<button
								on:click={navigateForward}
								disabled={!canNavigateForward}
								class="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors theme-button disabled:opacity-50 disabled:cursor-not-allowed"
								aria-label="Next page"
								title="Next page"
							>
								<ChevronRight className="size-4 text-gray-600 dark:text-gray-400 theme-icon" />
							</button>
						</div>
					{/if}

					<div class="flex flex-col gap-1 flex-1 min-w-0">
						<div class="text-lg font-semibold text-gray-900 dark:text-white truncate">
							{getCurrentPage().title}
						</div>

						<!-- Editable URL field -->
						<div class="flex items-center gap-2">
							{#if isEditingUrl}
								<input
									type="url"
									bind:value={editableUrl}
									on:keydown={handleUrlKeyDown}
									on:blur={cancelEditingUrl}
									class="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
									placeholder="Enter URL..."
									autofocus
								/>
								<button
									on:click={saveEditedUrl}
									class="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
									title="Save URL"
								>
									Save
								</button>
								<button
									on:click={cancelEditingUrl}
									class="px-2 py-1 text-xs bg-gray-500 hover:bg-gray-600 text-white rounded transition-colors"
									title="Cancel"
								>
									Cancel
								</button>
							{:else}
								<button
									on:click={startEditingUrl}
									class="flex-1 text-left text-sm text-blue-600 dark:text-blue-400 hover:underline truncate"
									title="Click to edit URL"
								>
									{getCurrentPage().url || 'No URL'}
								</button>
								{#if getCurrentPage().url}
									<a
										href={getCurrentPage().url}
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
				</div>
				<div class="flex items-center gap-2 flex-shrink-0">
					<button
						on:click={handleReload}
						class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors theme-button"
						aria-label="Reload page"
						title="Reload page"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
							class="size-5 text-gray-600 dark:text-gray-400 theme-icon"
						>
							<path
								fill-rule="evenodd"
								d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm-3.068-9.93a7 7 0 00-11.712 3.138.75.75 0 101.449.39 5.5 5.5 0 019.201-2.466l.312.311h-2.433a.75.75 0 000 1.5h4.243a.75.75 0 00.75-.75V3.375a.75.75 0 00-1.5 0v2.43l-.31-.31z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
					<button
						on:click={minimizePreview}
						class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors theme-button"
						aria-label="Minimize preview"
						title="Minimize preview"
					>
						<Minus className="size-5 text-gray-600 dark:text-gray-400 theme-icon" />
					</button>
					<button
						on:click={() => (show = false)}
						class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors theme-button"
						aria-label="Close preview"
						title="Close preview"
					>
						<XMark className="size-5 text-gray-600 dark:text-gray-400 theme-icon" />
					</button>
				</div>
			</div>

			<!-- Loading indicator -->
			{#if isLoading}
				<div class="absolute inset-x-0 top-[73px] bottom-0 flex items-center justify-center bg-white dark:bg-gray-900 z-[1]">
					<div class="flex flex-col items-center gap-3">
						<div class="breathing-light rounded-full h-8 w-8"></div>
						<div class="text-sm text-gray-600 dark:text-gray-400">Loading documentation...</div>
					</div>
				</div>
			{/if}

			<!-- Iframe -->
			{#if getCurrentPage().url}
				<iframe
					bind:this={iframeElement}
					src={getCurrentPage().url}
					title={getCurrentPage().title}
					class="w-full h-full border-0"
					on:load={handleIframeLoad}
					sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
				></iframe>
			{/if}

			<!-- Bottom-left menu -->
			<div class="absolute bottom-4 left-4 z-10">
				{#if showBottomMenu}
					<div class="mb-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 min-w-[160px]">
						<button
							on:click={copyCurrentUrl}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
						>
							Copy URL
						</button>
						<button
							on:click={openInNewWindow}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
						>
							Open in New Window
						</button>
						<button
							on:click={printPage}
							class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
						>
							Print Page
						</button>
					</div>
				{/if}
				<button
					on:click={toggleBottomMenu}
					class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
					aria-label="Menu"
					title="Menu"
				>
					<svg class="size-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
					</svg>
				</button>
			</div>

			</div>
		</div>
	{/if}
{/if}

<style>
	iframe {
		height: calc(100% - 73px); /* Subtract header height */
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
			transform: scale(1.0);
			background-position: 100% 50%;
		}
		50% {
			opacity: 1;
			transform: scale(1.2);
			background-position: 50% 100%;
		}
		75% {
			opacity: 0.7;
			transform: scale(1.0);
			background-position: 0% 100%;
		}
		100% {
			opacity: 0.4;
			transform: scale(0.8);
			background-position: 0% 50%;
		}
	}

	/* Theme-aware button styles */
	:global(.theme-button) {
		background-color: var(--background-color, transparent) !important;
		border: 1px solid var(--border-color, #d1d5db) !important;
	}

	:global(.theme-button:hover) {
		background-color: var(--hover-background-color, #f3f4f6) !important;
		border-color: var(--hover-border-color, #9ca3af) !important;
	}

	:global(.theme-icon) {
		color: var(--text-color, #6b7280) !important;
	}

	/* Dark theme overrides */
	:global(html.dark .theme-button) {
		background-color: var(--background-color, transparent) !important;
		border-color: var(--border-color, #374151) !important;
	}

	:global(html.dark .theme-button:hover) {
		background-color: var(--hover-background-color, #374151) !important;
		border-color: var(--hover-border-color, #6b7280) !important;
	}

	:global(html.dark .theme-icon) {
		color: var(--text-color, #9ca3af) !important;
	}
</style>
