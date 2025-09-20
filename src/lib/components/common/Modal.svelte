<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	import { flyAndScale } from '$lib/utils/transitions';
	import * as FocusTrap from 'focus-trap';
	export let show = true;
	export let size = 'md';
	export let containerClassName = 'p-3';
	export let className = 'bg-white dark:bg-gray-900 rounded-3xl';
	export let draggable: boolean = true;

	let modalElement: HTMLDivElement | null = null;
	let contentElement: HTMLDivElement | null = null;
	let mounted = false;

	// Dragging state
	let isDragging = false;
	let dragOffset = { x: 0, y: 0 };
	let position = { x: 0, y: 0 };
	// Create focus trap to trap user tabs inside modal
	// https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html
	// https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html
	let focusTrap: FocusTrap.FocusTrap | null = null;

	const sizeToWidth = (size: string) => {
		if (size === 'full') {
			return 'w-full';
		}
		if (size === 'xs') {
			return 'w-[16rem]';
		} else if (size === 'sm') {
			return 'w-[30rem]';
		} else if (size === 'md') {
			return 'w-[42rem]';
		} else {
			return 'w-[56rem]';
		}
	};

	const handleKeyDown = (event: KeyboardEvent) => {
		if (event.key === 'Escape' && isTopModal()) {
			console.log('Escape');
			show = false;
		}
	};

	const isTopModal = () => {
		const modals = document.getElementsByClassName('modal');
		return modals.length && modals[modals.length - 1] === modalElement;
	};

	// Drag functionality
	const handleMouseDown = (event: MouseEvent) => {
		// Don't enable dragging if the target is an interactive element
		const target = event.target as HTMLElement;
		if (target.tagName === 'BUTTON' || target.tagName === 'A' || target.tagName === 'INPUT' ||
			target.tagName === 'SELECT' || target.tagName === 'TEXTAREA' ||
			target.closest('button') || target.closest('a') || target.closest('[role="button"]') ||
			target.closest('[role="tab"]') || target.closest('[role="menuitem"]')) {
			return;
		}

		if (!contentElement) return;

		isDragging = true;
		const rect = contentElement.getBoundingClientRect();
		dragOffset = {
			x: event.clientX - rect.left,
			y: event.clientY - rect.top
		};
		document.addEventListener('mousemove', handleMouseMove);
		document.addEventListener('mouseup', handleMouseUp);
		event.preventDefault();
		event.stopPropagation();
	};

	const handleMouseMove = (event: MouseEvent) => {
		if (isDragging) {
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

	onMount(() => {
		mounted = true;
	});

	$: if (show && modalElement) {
		document.body.appendChild(modalElement);
		focusTrap = FocusTrap.createFocusTrap(modalElement);
		focusTrap.activate();
		window.addEventListener('keydown', handleKeyDown);
		document.body.style.overflow = 'hidden';
		// Reset position when opening
		position = { x: 0, y: 0 };
	} else if (modalElement && focusTrap) {
		focusTrap.deactivate();
		window.removeEventListener('keydown', handleKeyDown);
		document.body.removeChild(modalElement);
		document.body.style.overflow = 'unset';
		// Clean up drag listeners if modal is closed while dragging
		if (isDragging) {
			handleMouseUp();
		}
	}

	onDestroy(() => {
		show = false;
		if (focusTrap) {
			focusTrap.deactivate();
		}
		if (modalElement) {
			document.body.removeChild(modalElement);
		}
	});
</script>

{#if show}


	<!-- svelte-ignore a11y-no-static-element-interactions -->
	<!-- svelte-ignore a11y-mouse-events-have-key-events -->
	<div
		bind:this={modalElement}
		aria-modal="true"
		role="dialog"
		class="modal fixed top-0 right-0 left-0 bottom-0 w-full h-screen max-h-[100dvh] {containerClassName} flex justify-center items-center z-[9997] overflow-y-auto overscroll-contain"
		in:fade={{ duration: 10 }}
		on:mousedown={(e) => {
			// Only close if clicking the backdrop, not the modal content
			if (e.target === e.currentTarget) {
				show = false;
			}
		}}
	>
		<!-- svelte-ignore a11y-no-static-element-interactions -->
		<!-- svelte-ignore a11y-mouse-events-have-key-events -->
		<div
			bind:this={contentElement}
			class="max-w-full {sizeToWidth(size)} {size !== 'full'
				? 'mx-2'
				: ''} shadow-3xl min-h-fit scrollbar-hidden {className} menu-cover {draggable ? 'cursor-move' : ''}"
			style="transform: translate({position.x}px, {position.y}px)"
			in:flyAndScale
			on:mousedown={(e) => {
				e.stopPropagation();
				if (draggable) {
					handleMouseDown(e);
				}
			}}
			role="dialog"
			tabindex="-1"
		>
			<slot />
		</div>
	</div>
{/if}

<style>
	.modal-content {
		animation: scaleUp 0.1s ease-out forwards;
	}

	@keyframes scaleUp {
		from {
			transform: scale(0.985);
			opacity: 0;
		}
		to {
			transform: scale(1);
			opacity: 1;
		}
	}
</style>
