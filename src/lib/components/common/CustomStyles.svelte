<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { user } from '$lib/stores';

	let customCSS = '';
	let customJS = '';
	let styleElement: HTMLStyleElement | null = null;
	let scriptElement: HTMLScriptElement | null = null;

	const loadCustomStyles = () => {
		try {
			// Load from localStorage (pure frontend solution)
			customCSS = localStorage.getItem('customCSS') || '';
			customJS = localStorage.getItem('customJS') || '';
			applyCustomStyles();
		} catch (error) {
			console.error('Failed to load custom styles:', error);
		}
	};

	const applyCustomStyles = () => {
		// Apply custom CSS
		if (customCSS) {
			// Remove existing custom style element
			if (styleElement) {
				styleElement.remove();
			}

			// Create new style element
			styleElement = document.createElement('style');
			styleElement.setAttribute('data-custom-css', 'true');
			styleElement.textContent = customCSS;
			document.head.appendChild(styleElement);
		}

		// Apply custom JavaScript
		if (customJS) {
			// Remove existing custom script element
			if (scriptElement) {
				scriptElement.remove();
			}

			// Create new script element
			scriptElement = document.createElement('script');
			scriptElement.setAttribute('data-custom-js', 'true');
			scriptElement.textContent = customJS;
			document.head.appendChild(scriptElement);
		}
	};

	const removeCustomStyles = () => {
		// Remove custom CSS
		if (styleElement) {
			styleElement.remove();
			styleElement = null;
		}

		// Remove custom JavaScript
		if (scriptElement) {
			scriptElement.remove();
			scriptElement = null;
		}
	};

	const handleCustomStylesUpdate = (event: Event) => {
		const customEvent = event as CustomEvent;
		customCSS = customEvent.detail?.customCSS || '';
		customJS = customEvent.detail?.customJS || '';
		applyCustomStyles();
	};

	onMount(() => {
		loadCustomStyles();
		// Listen for custom styles updates
		window.addEventListener('customStylesUpdated', handleCustomStylesUpdate);
	});

	onDestroy(() => {
		removeCustomStyles();
		// Remove event listener
		window.removeEventListener('customStylesUpdated', handleCustomStylesUpdate);
	});

	// Reactive statement to reload styles when user changes
	$: if ($user) {
		loadCustomStyles();
	}
</script>

<!-- This component doesn't render anything visible -->
