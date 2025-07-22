/**
 * Material Design theme generator based on dominant colors
 */

import {
	type RGB,
	type HSL,
	type ColorPalette,
	rgbToHsl,
	hslToRgb,
	rgbToHex,
	isLightColor,
	getContrastRatio
} from './colorAnalysis';

/**
 * Generate Material Design color palette from dominant colors
 */
export function generateMaterialPalette(dominantColors: RGB[]): ColorPalette {
	if (dominantColors.length === 0) {
		// Fallback to default Material Design colors
		// Fallback to CSS variables if no dominant colors are found
		return {
			primary: 'var(--md-sys-color-primary)',
			primaryVariant: 'var(--md-sys-color-primary-variant)',
			secondary: 'var(--md-sys-color-secondary)',
			secondaryVariant: 'var(--md-sys-color-secondary-variant)',
			background: 'var(--md-sys-color-background)',
			surface: 'var(--md-sys-color-surface)',
			error: 'var(--md-sys-color-error)',
			onPrimary: 'var(--md-sys-color-on-primary)',
			onSecondary: 'var(--md-sys-color-on-secondary)',
			onBackground: 'var(--md-sys-color-on-background)',
			onSurface: 'var(--md-sys-color-on-surface)',
			onError: 'var(--md-sys-color-on-error)'
		};
	}

	const primaryColor = dominantColors[0];
	const secondaryColor = dominantColors[1] || generateComplementaryColor(primaryColor);

	// Convert to HSL for easier manipulation
	const primaryHsl = rgbToHsl(primaryColor.r, primaryColor.g, primaryColor.b);
	const secondaryHsl = rgbToHsl(secondaryColor.r, secondaryColor.g, secondaryColor.b);

	// Generate primary variants
	const primaryVariant = generateColorVariant(primaryHsl, -20, 0, -10); // Darker variant
	const secondaryVariant = generateColorVariant(secondaryHsl, 20, 0, 10); // Lighter variant

	// Determine if we should use light or dark theme based on primary color
	const isLightTheme = isLightColor(primaryColor.r, primaryColor.g, primaryColor.b);

	// Generate background and surface colors
	const background = isLightTheme 
		? { r: 250, g: 250, b: 250 } // Light background
		: { r: 18, g: 18, b: 18 }; // Dark background

	const surface = isLightTheme
		? { r: 255, g: 255, b: 255 } // Light surface
		: { r: 30, g: 30, b: 30 }; // Dark surface

	// Error color (Material Design standard)
	const error = { r: 176, g: 0, b: 32 };

	// Generate "on" colors (text colors that work on colored backgrounds)
	const onPrimary = getOptimalTextColor(primaryColor);
	const onSecondary = getOptimalTextColor(secondaryColor);
	const onBackground = isLightTheme ? { r: 33, g: 33, b: 33 } : { r: 255, g: 255, b: 255 };
	const onSurface = isLightTheme ? { r: 33, g: 33, b: 33 } : { r: 255, g: 255, b: 255 };
	const onError = { r: 255, g: 255, b: 255 };

	return {
		primary: rgbToHex(primaryColor.r, primaryColor.g, primaryColor.b),
		primaryVariant: rgbToHex(primaryVariant.r, primaryVariant.g, primaryVariant.b),
		secondary: rgbToHex(secondaryColor.r, secondaryColor.g, secondaryColor.b),
		secondaryVariant: rgbToHex(secondaryVariant.r, secondaryVariant.g, secondaryVariant.b),
		background: rgbToHex(background.r, background.g, background.b),
		surface: rgbToHex(surface.r, surface.g, surface.b),
		error: rgbToHex(error.r, error.g, error.b),
		onPrimary: rgbToHex(onPrimary.r, onPrimary.g, onPrimary.b),
		onSecondary: rgbToHex(onSecondary.r, onSecondary.g, onSecondary.b),
		onBackground: rgbToHex(onBackground.r, onBackground.g, onBackground.b),
		onSurface: rgbToHex(onSurface.r, onSurface.g, onSurface.b),
		onError: rgbToHex(onError.r, onError.g, onError.b)
	};
}

/**
 * Generate a color variant by adjusting HSL values
 */
function generateColorVariant(hsl: HSL, hueShift: number, satShift: number, lightShift: number): RGB {
	const newHsl: HSL = {
		h: (hsl.h + hueShift + 360) % 360,
		s: Math.max(0, Math.min(100, hsl.s + satShift)),
		l: Math.max(0, Math.min(100, hsl.l + lightShift))
	};
	return hslToRgb(newHsl.h, newHsl.s, newHsl.l);
}

/**
 * Generate a complementary color
 */
function generateComplementaryColor(color: RGB): RGB {
	const hsl = rgbToHsl(color.r, color.g, color.b);
	const complementaryHsl: HSL = {
		h: (hsl.h + 180) % 360,
		s: hsl.s,
		l: hsl.l
	};
	return hslToRgb(complementaryHsl.h, complementaryHsl.s, complementaryHsl.l);
}

/**
 * Get optimal text color (black or white) for a given background color
 */
function getOptimalTextColor(backgroundColor: RGB): RGB {
	const whiteText = { r: 255, g: 255, b: 255 };
	const blackText = { r: 0, g: 0, b: 0 };

	const whiteContrast = getContrastRatio(backgroundColor, whiteText);
	const blackContrast = getContrastRatio(backgroundColor, blackText);

	// Return the color with better contrast (minimum 4.5:1 for AA compliance)
	return whiteContrast > blackContrast ? whiteText : blackText;
}

/**
 * Get default Material Design palette
 */

/**
 * Apply Material Design theme to CSS custom properties
 */
export function applyMaterialTheme(palette?: ColorPalette, isDark = false): void {
	const root = document.documentElement;

	if (palette) {
		// Apply Material Design colors from palette
		root.style.setProperty('--md-primary', palette.primary);
		root.style.setProperty('--md-primary-variant', palette.primaryVariant);
		root.style.setProperty('--md-secondary', palette.secondary);
		root.style.setProperty('--md-secondary-variant', palette.secondaryVariant);
		root.style.setProperty('--md-background', palette.background);
		root.style.setProperty('--md-surface', palette.surface);
		root.style.setProperty('--md-error', palette.error);
		root.style.setProperty('--md-on-primary', palette.onPrimary);
		root.style.setProperty('--md-on-secondary', palette.onSecondary);
		root.style.setProperty('--md-on-background', palette.onBackground);
		root.style.setProperty('--md-on-surface', palette.onSurface);
		root.style.setProperty('--md-on-error', palette.onError);

		// Map to existing Tailwind color variables for compatibility
		root.style.setProperty('--color-primary', palette.primary);
		root.style.setProperty('--color-secondary', palette.secondary);

		// Update button colors
		root.style.setProperty('--color-button-primary', palette.primary);
		root.style.setProperty('--color-button-primary-hover', palette.primaryVariant);
		root.style.setProperty('--color-button-secondary', palette.secondary);
		root.style.setProperty('--color-button-secondary-hover', palette.secondaryVariant);

		// Update text colors
		root.style.setProperty('--color-text-primary', palette.onBackground);
		root.style.setProperty('--color-text-secondary', palette.onSurface);

		// Store the palette for future reference
		(window as any).currentMaterialPalette = palette;
	}

	// Add Material Design theme class
	root.classList.add('md-theme');
}

/**
 * Remove Material Design theme
 */
export function removeMaterialTheme(): void {
	const root = document.documentElement;
	
	// Remove Material Design CSS variables
	const mdProperties = [
		'--md-primary', '--md-primary-variant', '--md-secondary', '--md-secondary-variant',
		'--md-background', '--md-surface', '--md-error', '--md-on-primary', '--md-on-secondary',
		'--md-on-background', '--md-on-surface', '--md-on-error', '--color-primary', '--color-secondary',
		'--color-button-primary', '--color-button-primary-hover', '--color-button-secondary',
		'--color-button-secondary-hover', '--color-text-primary', '--color-text-secondary'
	];

	mdProperties.forEach(prop => root.style.removeProperty(prop));
	root.classList.remove('md-theme');
	
	delete (window as any).currentMaterialPalette;
}

/**
 * Generate theme from background image/video URL
 */
export async function generateThemeFromBackground(backgroundUrl: string): Promise<ColorPalette> {
	try {
		let dominantColors: RGB[];
		
		if (backgroundUrl.endsWith('.mp4')) {
			// Handle video
			const { extractVideoColors } = await import('./colorAnalysis');
			dominantColors = await extractVideoColors(backgroundUrl);
		} else {
			// Handle image
			const { extractDominantColors } = await import('./colorAnalysis');
			dominantColors = await extractDominantColors(backgroundUrl);
		}

		return generateMaterialPalette(dominantColors);
	} catch (error) {
		console.error('Failed to generate theme from background:', error);
		// Return a default palette based on CSS variables if image processing fails
		return {
			primary: 'var(--md-sys-color-primary)',
			primaryVariant: 'var(--md-sys-color-primary-variant)',
			secondary: 'var(--md-sys-color-secondary)',
			secondaryVariant: 'var(--md-sys-color-secondary-variant)',
			background: 'var(--md-sys-color-background)',
			surface: 'var(--md-sys-color-surface)',
			error: 'var(--md-sys-color-error)',
			onPrimary: 'var(--md-sys-color-on-primary)',
			onSecondary: 'var(--md-sys-color-on-secondary)',
			onBackground: 'var(--md-sys-color-on-background)',
			onSurface: 'var(--md-sys-color-on-surface)',
			onError: 'var(--md-sys-color-on-error)'
		};
	}
}
