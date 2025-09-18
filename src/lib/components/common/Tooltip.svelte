<script lang="ts">
	import DOMPurify from 'dompurify';

	import { onDestroy } from 'svelte';
	import { theme as currentTheme } from '$lib/stores';

	import tippy from 'tippy.js';

	export let elementId = '';

	export let as = 'div';
	export let className = 'flex';

	export let placement = 'top';
	export let content = `I'm a tooltip!`;
	export let touch = true;
	export let theme = '';
	export let offset = [0, 4];
	export let allowHTML = true;
	export let tippyOptions = {};

	export let onClick = () => {};

	let tooltipElement;
	let tooltipInstance;

	// Function to get the appropriate tippy theme based on current app theme
	const getTippyTheme = (appTheme: string, customTheme: string): string => {
		if (customTheme !== '') {
			return customTheme;
		}

		// Map app themes to tippy themes
		const themeMap: Record<string, string> = {
			'light': 'light',
			'dark': 'dark',
			'oled-dark': 'oled',
			'rose-pine': 'rose-pine',
			'material-design': 'material',
			'pink-theme': 'pink',
			'her': 'her',
			'system': 'dark' // fallback for system theme
		};

		return themeMap[appTheme] || 'dark';
	};

	$: tippyTheme = getTippyTheme($currentTheme, theme);

	$: if (tooltipElement && content) {
		if (tooltipInstance) {
			tooltipInstance.setContent(DOMPurify.sanitize(content));
			// Update theme when it changes
			tooltipInstance.setProps({ theme: tippyTheme });
		} else {
			tooltipInstance = tippy(tooltipElement, {
				content: DOMPurify.sanitize(content),
				placement: placement as any,
				allowHTML: allowHTML,
				touch: touch,
				theme: tippyTheme,
				arrow: false,
				offset: offset as any,
				...tippyOptions
			});
		}
	} else if (tooltipInstance && content === '') {
		if (tooltipInstance) {
			tooltipInstance.destroy();
		}
	}

	// Update theme when currentTheme changes
	$: if (tooltipInstance && tippyTheme) {
		tooltipInstance.setProps({ theme: tippyTheme });
	}

	onDestroy(() => {
		if (tooltipInstance) {
			tooltipInstance.destroy();
		}
	});
</script>

<!-- svelte-ignore a11y-no-static-element-interactions -->
<svelte:element this={as} bind:this={tooltipElement} class={className} on:click={onClick}>
	<slot />
</svelte:element>

<slot name="tooltip"></slot>
