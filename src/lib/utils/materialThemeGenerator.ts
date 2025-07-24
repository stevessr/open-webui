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

// Import the new theme manager
import { ThemeManager } from './themeManager';

/**
 * Generate Material Design color palette from dominant colors
 */
export function generateMaterialPalette(dominantColors: RGB[]): ColorPalette {
	if (dominantColors.length === 0) {
		// Fallback to default macaron colors
		return {
			primary: '#FFB6C1',     // Light Pink (macaron pink)
			primaryVariant: '#FF91A4', // Deeper Pink
			secondary: '#B8E6B8',   // Mint Green (macaron green)
			secondaryVariant: '#98D982', // Deeper Mint
			background: '#FFF8F0',  // Cream (macaron cream)
			surface: '#FFFFFF',     // White
			error: '#FFB3BA',       // Soft Red (macaron red)
			onPrimary: '#FFFFFF',   // White text on primary
			onSecondary: '#2D5016', // Dark green text on secondary
			onBackground: '#5D4E37', // Brown text on background
			onSurface: '#5D4E37',   // Brown text on surface
			onError: '#8B0000'      // Dark red text on error
		};
	}

	// Filter out colors that are too dark or too light for good UI
	const filteredColors = dominantColors.filter(color => {
		const luminance = getLuminance(color);
		return luminance > 0.1 && luminance < 0.9; // Keep colors with good contrast potential
	});

	// If no suitable colors found, fall back to macaron theme
	if (filteredColors.length === 0) {
		return generateMaterialPalette([]);
	}

	// Sort colors by saturation and lightness for better selection
	const sortedColors = filteredColors.sort((a, b) => {
		const aHsl = rgbToHsl(a.r, a.g, a.b);
		const bHsl = rgbToHsl(b.r, b.g, b.b);
		// Prefer colors with good saturation and moderate lightness
		const aScore = aHsl.s * (1 - Math.abs(aHsl.l - 0.5));
		const bScore = bHsl.s * (1 - Math.abs(bHsl.l - 0.5));
		return bScore - aScore;
	});

	const primaryColor = sortedColors[0];
	let secondaryColor: RGB;

	// Try to find a good secondary color from the palette
	if (sortedColors.length > 1) {
		// Look for a color that's complementary or analogous to the primary
		const primaryHsl = rgbToHsl(primaryColor.r, primaryColor.g, primaryColor.b);

		let bestSecondary = sortedColors[1];
		let bestScore = 0;

		for (let i = 1; i < Math.min(sortedColors.length, 5); i++) {
			const candidateHsl = rgbToHsl(sortedColors[i].r, sortedColors[i].g, sortedColors[i].b);
			const hueDiff = Math.abs(primaryHsl.h - candidateHsl.h);
			const normalizedHueDiff = Math.min(hueDiff, 360 - hueDiff);

			// Prefer complementary (150-210°) or analogous (30-60°) colors
			let score = 0;
			if (normalizedHueDiff >= 150 && normalizedHueDiff <= 210) {
				score = 2; // Complementary
			} else if (normalizedHueDiff >= 30 && normalizedHueDiff <= 60) {
				score = 1.5; // Analogous
			} else {
				score = 1 / (normalizedHueDiff + 1); // Closer is better for other cases
			}

			// Boost score for good saturation and lightness
			score *= candidateHsl.s * (1 - Math.abs(candidateHsl.l - 0.5));

			if (score > bestScore) {
				bestScore = score;
				bestSecondary = sortedColors[i];
			}
		}
		secondaryColor = bestSecondary;
	} else {
		secondaryColor = generateComplementaryColor(primaryColor);
	}

	// Convert to HSL for easier manipulation
	const primaryHsl = rgbToHsl(primaryColor.r, primaryColor.g, primaryColor.b);
	const secondaryHsl = rgbToHsl(secondaryColor.r, secondaryColor.g, secondaryColor.b);

	// Generate variants with better color harmony
	const primaryVariant = generateColorVariant(primaryHsl, -15, 0.1, -0.1); // Slightly darker and more saturated
	const secondaryVariant = generateColorVariant(secondaryHsl, 15, 0.1, 0.1); // Slightly lighter and more saturated

	// Determine theme brightness based on average luminance of dominant colors
	const avgLuminance = filteredColors.reduce((sum, color) => sum + getLuminance(color), 0) / filteredColors.length;
	const isLightTheme = avgLuminance > 0.5;

	// Generate background and surface colors with subtle tinting from primary color
	let background: RGB, surface: RGB;

	if (isLightTheme) {
		// Light theme with subtle primary color tint
		const tintStrength = 0.02; // Very subtle tint
		background = {
			r: Math.round(255 - (255 - primaryColor.r) * tintStrength),
			g: Math.round(255 - (255 - primaryColor.g) * tintStrength),
			b: Math.round(255 - (255 - primaryColor.b) * tintStrength)
		};
		surface = { r: 255, g: 255, b: 255 }; // Pure white surface
	} else {
		// Dark theme with subtle primary color tint
		const tintStrength = 0.05;
		background = {
			r: Math.round(18 + primaryColor.r * tintStrength),
			g: Math.round(18 + primaryColor.g * tintStrength),
			b: Math.round(18 + primaryColor.b * tintStrength)
		};
		surface = {
			r: Math.round(30 + primaryColor.r * tintStrength),
			g: Math.round(30 + primaryColor.g * tintStrength),
			b: Math.round(30 + primaryColor.b * tintStrength)
		};
	}

	// Generate error color that harmonizes with the palette
	const errorColor = generateColorVariant(
		{ h: 0, s: 0.7, l: isLightTheme ? 0.6 : 0.4 }, // Red-based error color
		0, 0, 0
	);
	const error = errorColor;

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
 * Calculate luminance of a color (0-1 scale)
 */
function getLuminance(color: RGB): number {
	// Convert RGB to linear RGB
	const r = color.r / 255;
	const g = color.g / 255;
	const b = color.b / 255;

	// Apply gamma correction
	const rLinear = r <= 0.03928 ? r / 12.92 : Math.pow((r + 0.055) / 1.055, 2.4);
	const gLinear = g <= 0.03928 ? g / 12.92 : Math.pow((g + 0.055) / 1.055, 2.4);
	const bLinear = b <= 0.03928 ? b / 12.92 : Math.pow((b + 0.055) / 1.055, 2.4);

	// Calculate luminance using ITU-R BT.709 coefficients
	return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
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

		// Apply additional macaron color scheme variables
		root.style.setProperty('--md-tertiary', '#E6D7FF');    // Lavender
		root.style.setProperty('--md-tertiary-variant', '#D1C4E9'); // Deeper Lavender
		root.style.setProperty('--md-surface-variant', '#F5F5DC'); // Beige
		root.style.setProperty('--md-warning', '#FFE4B5');     // Moccasin
		root.style.setProperty('--md-success', palette.secondary); // Use secondary for consistency
		root.style.setProperty('--md-info', '#B3E5FC');        // Light Blue
		root.style.setProperty('--md-on-tertiary', '#4A148C');  // Deep purple
		root.style.setProperty('--md-on-surface-variant', '#6D4C41'); // Darker brown
		root.style.setProperty('--md-on-warning', '#8B4513');   // Saddle brown
		root.style.setProperty('--md-on-success', palette.onSecondary); // Consistent with secondary
		root.style.setProperty('--md-on-info', '#0D47A1');      // Dark blue

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

	// Initialize Material Design ripple effects
	import('./materialRipple').then(({ initializeMaterialRipples }) => {
		initializeMaterialRipples();
	});
}

/**
 * Remove Material Design theme
 */
export function removeMaterialTheme(): void {
	const root = document.documentElement;
	
	// Remove Material Design CSS variables
	const mdProperties = [
		'--md-primary', '--md-primary-variant', '--md-secondary', '--md-secondary-variant',
		'--md-tertiary', '--md-tertiary-variant', '--md-background', '--md-surface', '--md-surface-variant',
		'--md-error', '--md-warning', '--md-success', '--md-info', '--md-on-primary', '--md-on-secondary',
		'--md-on-tertiary', '--md-on-background', '--md-on-surface', '--md-on-surface-variant',
		'--md-on-error', '--md-on-warning', '--md-on-success', '--md-on-info',
		'--color-primary', '--color-secondary', '--color-button-primary', '--color-button-primary-hover',
		'--color-button-secondary', '--color-button-secondary-hover', '--color-text-primary', '--color-text-secondary'
	];

	mdProperties.forEach(prop => root.style.removeProperty(prop));
	root.classList.remove('md-theme');

	// Clean up Material Design ripple effects
	import('./materialRipple').then(({ cleanupMaterialRipples }) => {
		cleanupMaterialRipples();
	});

	delete (window as any).currentMaterialPalette;
}

// Cache for generated themes to improve performance
const themeCache = new Map<string, { palette: ColorPalette; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

/**
 * Generate theme from background image/video URL with caching
 */
export async function generateThemeFromBackground(backgroundUrl: string): Promise<ColorPalette> {
	// Check cache first
	const cached = themeCache.get(backgroundUrl);
	if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
		return cached.palette;
	}

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

		const palette = generateMaterialPalette(dominantColors);

		// Cache the result
		themeCache.set(backgroundUrl, { palette, timestamp: Date.now() });

		// Clean up old cache entries
		if (themeCache.size > 50) { // Limit cache size
			const oldestKey = Array.from(themeCache.keys())[0];
			themeCache.delete(oldestKey);
		}

		return palette;
	} catch (error) {
		console.error('Failed to generate theme from background:', error);
		// Return default macaron palette if image processing fails
		const fallbackPalette = {
			primary: '#FFB6C1',     // Light Pink (macaron pink)
			primaryVariant: '#FF91A4', // Deeper Pink
			secondary: '#B8E6B8',   // Mint Green (macaron green)
			secondaryVariant: '#98D982', // Deeper Mint
			background: '#FFF8F0',  // Cream (macaron cream)
			surface: '#FFFFFF',     // White
			error: '#FFB3BA',       // Soft Red (macaron red)
			onPrimary: '#FFFFFF',   // White text on primary
			onSecondary: '#2D5016', // Dark green text on secondary
			onBackground: '#5D4E37', // Brown text on background
			onSurface: '#5D4E37',   // Brown text on surface
			onError: '#8B0000'      // Dark red text on error
		};

		// Cache the fallback too
		themeCache.set(backgroundUrl, { palette: fallbackPalette, timestamp: Date.now() });

		return fallbackPalette;
	}
}

/**
 * Clear the theme cache
 */
export function clearThemeCache(): void {
	themeCache.clear();
}
