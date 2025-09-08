/**
 * Color analysis utility for extracting dominant colors from images and videos
 * and generating Material Design color palettes
 */

export interface ColorPalette {
	primary: string;
	primaryVariant: string;
	secondary: string;
	secondaryVariant: string;
	background: string;
	surface: string;
	error: string;
	onPrimary: string;
	onSecondary: string;
	onBackground: string;
	onSurface: string;
	onError: string;
}

export interface RGB {
	r: number;
	g: number;
	b: number;
}

export interface HSL {
	h: number;
	s: number;
	l: number;
}

/**
 * Convert RGB to HSL
 */
export function rgbToHsl(r: number, g: number, b: number): HSL {
	r /= 255;
	g /= 255;
	b /= 255;

	const max = Math.max(r, g, b);
	const min = Math.min(r, g, b);
	let h = 0;
	let s = 0;
	const l = (max + min) / 2;

	if (max === min) {
		h = s = 0; // achromatic
	} else {
		const d = max - min;
		s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

		switch (max) {
			case r:
				h = (g - b) / d + (g < b ? 6 : 0);
				break;
			case g:
				h = (b - r) / d + 2;
				break;
			case b:
				h = (r - g) / d + 4;
				break;
		}
		h /= 6;
	}

	return { h: h * 360, s: s * 100, l: l * 100 };
}

/**
 * Convert HSL to RGB
 */
export function hslToRgb(h: number, s: number, l: number): RGB {
	h /= 360;
	s /= 100;
	l /= 100;

	const hue2rgb = (p: number, q: number, t: number) => {
		if (t < 0) t += 1;
		if (t > 1) t -= 1;
		if (t < 1 / 6) return p + (q - p) * 6 * t;
		if (t < 1 / 2) return q;
		if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
		return p;
	};

	let r, g, b;

	if (s === 0) {
		r = g = b = l; // achromatic
	} else {
		const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
		const p = 2 * l - q;
		r = hue2rgb(p, q, h + 1 / 3);
		g = hue2rgb(p, q, h);
		b = hue2rgb(p, q, h - 1 / 3);
	}

	return {
		r: Math.round(r * 255),
		g: Math.round(g * 255),
		b: Math.round(b * 255)
	};
}

/**
 * Convert RGB to hex color
 */
export function rgbToHex(r: number, g: number, b: number): string {
	return '#' + [r, g, b].map((x) => x.toString(16).padStart(2, '0')).join('');
}

/**
 * Calculate color luminance
 */
export function getLuminance(r: number, g: number, b: number): number {
	const [rs, gs, bs] = [r, g, b].map((c) => {
		c = c / 255;
		return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
	});
	return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

/**
 * Calculate contrast ratio between two colors
 */
export function getContrastRatio(color1: RGB, color2: RGB): number {
	const lum1 = getLuminance(color1.r, color1.g, color1.b);
	const lum2 = getLuminance(color2.r, color2.g, color2.b);
	const brightest = Math.max(lum1, lum2);
	const darkest = Math.min(lum1, lum2);
	return (brightest + 0.05) / (darkest + 0.05);
}

/**
 * Check if a color is light or dark
 */
export function isLightColor(r: number, g: number, b: number): boolean {
	return getLuminance(r, g, b) > 0.5;
}

/**
 * Extract dominant colors from an image using canvas
 */
export async function extractDominantColors(imageUrl: string, sampleSize = 10): Promise<RGB[]> {
	return new Promise((resolve, reject) => {
		const img = new Image();
		img.crossOrigin = 'anonymous';

		img.onload = () => {
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');

			if (!ctx) {
				reject(new Error('Could not get canvas context'));
				return;
			}

			// Scale down image for faster processing
			const scale = Math.min(200 / img.width, 200 / img.height);
			canvas.width = img.width * scale;
			canvas.height = img.height * scale;

			ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

			const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
			const data = imageData.data;

			// Sample pixels and count colors
			const colorMap = new Map<string, number>();
			const step = Math.max(1, Math.floor(data.length / (sampleSize * 1000)));

			for (let i = 0; i < data.length; i += step * 4) {
				const r = data[i];
				const g = data[i + 1];
				const b = data[i + 2];
				const a = data[i + 3];

				// Skip transparent pixels
				if (a < 128) continue;

				// Group similar colors
				const key = `${Math.floor(r / 10) * 10},${Math.floor(g / 10) * 10},${Math.floor(b / 10) * 10}`;
				colorMap.set(key, (colorMap.get(key) || 0) + 1);
			}

			// Get most frequent colors
			const sortedColors = Array.from(colorMap.entries())
				.sort((a, b) => b[1] - a[1])
				.slice(0, 5)
				.map(([color]) => {
					const [r, g, b] = color.split(',').map(Number);
					return { r, g, b };
				});

			resolve(sortedColors);
		};

		img.onerror = () => reject(new Error('Failed to load image'));
		img.src = imageUrl;
	});
}

/**
 * Extract dominant color from video by analyzing the first frame
 */
export async function extractVideoColors(videoUrl: string): Promise<RGB[]> {
	return new Promise((resolve, reject) => {
		const video = document.createElement('video');
		video.crossOrigin = 'anonymous';
		video.muted = true;

		video.onloadeddata = () => {
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');

			if (!ctx) {
				reject(new Error('Could not get canvas context'));
				return;
			}

			canvas.width = video.videoWidth;
			canvas.height = video.videoHeight;
			ctx.drawImage(video, 0, 0);

			// Convert canvas to data URL and extract colors
			const dataUrl = canvas.toDataURL();
			extractDominantColors(dataUrl).then(resolve).catch(reject);
		};

		video.onerror = () => reject(new Error('Failed to load video'));
		video.src = videoUrl;
	});
}
