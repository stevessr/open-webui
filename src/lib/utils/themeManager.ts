/**
 * Theme Manager - Class-based theme system
 * Replaces CSS file loading with dynamic class application
 */

export interface ThemeConfig {
	name: string;
	displayName: string;
	baseTheme: 'light' | 'dark';
	cssVariables: Record<string, string>;
	classes: string[];
	metaThemeColor: string;
}

export interface ThemeDefinition {
	[key: string]: ThemeConfig;
}

// Define all themes with their configurations
export const THEME_DEFINITIONS: ThemeDefinition = {
	light: {
		name: 'light',
		displayName: 'Light',
		baseTheme: 'light',
		cssVariables: {
			'--background-color': '#f9fafb',
			'--text-color': '#374151',
			'--border-color': '#d1d5db',
			'--background': '0 0% 100%',
			'--foreground': '222.2 84% 4.9%',
			'--card': '0 0% 100%',
			'--card-foreground': '222.2 84% 4.9%',
			'--primary': '222.2 47.4% 11.2%',
			'--primary-foreground': '210 40% 98%',
			'--secondary': '210 40% 96.1%',
			'--secondary-foreground': '222.2 47.4% 11.2%',
			'--muted': '210 40% 96.1%',
			'--muted-foreground': '215.4 16.3% 46.9%',
			'--accent': '210 40% 96.1%',
			'--accent-foreground': '222.2 47.4% 11.2%',
			'--destructive': '0 84.2% 60.2%',
			'--destructive-foreground': '210 40% 98%',
			'--border': '214.3 31.8% 91.4%',
			'--input': '214.3 31.8% 91.4%',
			'--ring': '222.2 84% 4.9%'
		},
		classes: ['light'],
		metaThemeColor: '#ffffff'
	},
	dark: {
		name: 'dark',
		displayName: 'Dark',
		baseTheme: 'dark',
		cssVariables: {
			'--background-color': '#1f2937',
			'--text-color': '#d1d5db',
			'--border-color': '#374151',
			'--background': '222.2 84% 4.9%',
			'--foreground': '210 40% 98%',
			'--card': '222.2 84% 4.9%',
			'--card-foreground': '210 40% 98%',
			'--primary': '210 40% 98%',
			'--primary-foreground': '222.2 47.4% 11.2%',
			'--secondary': '217.2 32.6% 17.5%',
			'--secondary-foreground': '210 40% 98%',
			'--muted': '217.2 32.6% 17.5%',
			'--muted-foreground': '215 20.2% 65.1%',
			'--accent': '217.2 32.6% 17.5%',
			'--accent-foreground': '210 40% 98%',
			'--destructive': '0 62.8% 30.6%',
			'--destructive-foreground': '210 40% 98%',
			'--border': '217.2 32.6% 17.5%',
			'--input': '217.2 32.6% 17.5%',
			'--ring': '212.7 26.8% 83.9%'
		},
		classes: ['dark'],
		metaThemeColor: '#171717'
	},
	'oled-dark': {
		name: 'oled-dark',
		displayName: 'OLED Dark',
		baseTheme: 'dark',
		cssVariables: {
			'--background-color': '#000000',
			'--text-color': '#d1d5db',
			'--border-color': '#374151',
			'--color-gray-800': '#101010',
			'--color-gray-850': '#050505',
			'--color-gray-900': '#000000',
			'--color-gray-950': '#000000',
			'--background': '0 0% 0%',
			'--foreground': '210 40% 98%',
			'--card': '0 0% 0%',
			'--border': '217.2 32.6% 17.5%'
		},
		classes: ['dark', 'oled-dark'],
		metaThemeColor: '#000000'
	},
	'rose-pine': {
		name: 'rose-pine',
		displayName: 'Rose Pine',
		baseTheme: 'dark',
		cssVariables: {
			'--background-color': '#191724',
			'--text-color': '#e0def4',
			'--border-color': '#26233a',
			'--primary-color': '#c4a7e7',
			'--secondary-color': '#907aa9',
			'--surface-color': '#1f1d2e',
			'--nav-background': '#191724',
			'--chat-input-background': '#393552',
			'--gradient-background': '#26233a',
			'--background': '222.2 84% 4.9%',
			'--foreground': '210 40% 98%',
			'--card': '222.2 84% 4.9%',
			'--card-foreground': '210 40% 98%',
			'--primary': '210 40% 98%',
			'--primary-foreground': '222.2 47.4% 11.2%',
			'--secondary': '217.2 32.6% 17.5%',
			'--secondary-foreground': '210 40% 98%'
		},
		classes: ['dark', 'rose-pine'],
		metaThemeColor: '#191724'
	},
	her: {
		name: 'her',
		displayName: 'Her',
		baseTheme: 'dark',
		cssVariables: {
			'--background-color': '#1a1a1a',
			'--text-color': '#e0e0e0',
			'--border-color': '#444444',
			'--accent-color': '#983724'
		},
		classes: ['dark', 'her'],
		metaThemeColor: '#983724'
	},
	'frosted-glass': {
		name: 'frosted-glass',
		displayName: 'Frosted Glass',
		baseTheme: 'light',
		cssVariables: {
			'--background-color': 'rgba(255, 255, 255, 0.1)',
			'--text-color': '#2d3748',
			'--border-color': 'rgba(255, 255, 255, 0.2)',
			'--surface-color': 'rgba(255, 255, 255, 0.15)',
			'--backdrop-blur': 'blur(20px)',
			'--glass-shadow': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
			'--background': '0 0% 100%',
			'--foreground': '222.2 84% 4.9%',
			'--card': '0 0% 100%',
			'--card-foreground': '222.2 84% 4.9%',
			'--primary': '222.2 47.4% 11.2%',
			'--primary-foreground': '210 40% 98%',
			'--secondary': '210 40% 96.1%',
			'--secondary-foreground': '222.2 47.4% 11.2%',
			'--muted': '210 40% 96.1%',
			'--muted-foreground': '215.4 16.3% 46.9%',
			'--accent': '210 40% 96.1%',
			'--accent-foreground': '222.2 47.4% 11.2%'
		},
		classes: ['light', 'frosted-glass'],
		metaThemeColor: 'rgba(255, 255, 255, 0.8)'
	},
	'material-design': {
		name: 'material-design',
		displayName: 'Material Design',
		baseTheme: 'light',
		cssVariables: {
			'--background-color': '#FFF8F0',
			'--text-color': '#5D4E37',
			'--border-color': '#E6D7FF',
			'--primary-color': '#FFB6C1',
			'--secondary-color': '#B8E6B8',
			'--md-primary': '#FFB6C1',
			'--md-primary-variant': '#FF91A4',
			'--md-secondary': '#B8E6B8',
			'--md-secondary-variant': '#98D982',
			'--md-tertiary': '#E6D7FF',
			'--md-tertiary-variant': '#D1C4E9',
			'--md-background': '#FFF8F0',
			'--md-surface': '#FFFFFF',
			'--md-surface-variant': '#F5F5DC',
			'--md-error': '#FFB3BA',
			'--md-warning': '#FFE4B5',
			'--md-success': '#B8E6B8',
			'--md-on-primary': '#FFFFFF',
			'--md-on-secondary': '#2D5016',
			'--md-on-background': '#5D4E37',
			'--md-on-surface': '#5D4E37'
		},
		classes: ['md-theme'],
		metaThemeColor: '#FFB6C1'
	},
	'material-design-transparent': {
		name: 'material-design-transparent',
		displayName: 'Material Design (Transparent)',
		baseTheme: 'light',
		cssVariables: {
			'--background-color': 'rgba(255, 248, 240, 0.8)',
			'--text-color': '#5D4E37',
			'--border-color': '#E6D7FF',
			'--primary-color': '#FFB6C1',
			'--secondary-color': '#B8E6B8',
			'--md-primary': '#FFB6C1',
			'--md-primary-variant': '#FF91A4',
			'--md-secondary': '#B8E6B8',
			'--md-secondary-variant': '#98D982',
			'--md-tertiary': '#E6D7FF',
			'--md-tertiary-variant': '#D1C4E9',
			'--md-background': 'rgba(255, 248, 240, 0.8)',
			'--md-surface': 'rgba(255, 255, 255, 0.9)',
			'--md-surface-variant': 'rgba(245, 245, 220, 0.8)',
			'--md-error': '#FFB3BA',
			'--md-warning': '#FFE4B5',
			'--md-success': '#B8E6B8',
			'--md-on-primary': '#FFFFFF',
			'--md-on-secondary': '#2D5016',
			'--md-on-background': '#5D4E37',
			'--md-on-surface': '#5D4E37'
		},
		classes: ['md-theme', 'transparent'],
		metaThemeColor: 'rgba(255, 182, 193, 0.8)'
	}
};

export class ThemeManager {
	private static instance: ThemeManager;
	private currentTheme: string = 'system';
	private systemPrefersDark: boolean = false;

	private constructor() {
		if (typeof window !== 'undefined') {
			this.systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
			this.setupSystemThemeListener();
		}
	}

	public static getInstance(): ThemeManager {
		if (!ThemeManager.instance) {
			ThemeManager.instance = new ThemeManager();
		}
		return ThemeManager.instance;
	}

	private setupSystemThemeListener(): void {
		if (typeof window === 'undefined') return;

		window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
			this.systemPrefersDark = e.matches;
			if (this.currentTheme === 'system') {
				this.applyTheme('system');
			}
		});
	}

	private resolveTheme(themeName: string): string {
		if (themeName === 'system') {
			return this.systemPrefersDark ? 'dark' : 'light';
		}
		return themeName;
	}

	private clearAllThemeClasses(): void {
		if (typeof document === 'undefined') return;

		const root = document.documentElement;
		
		// Remove all theme classes
		Object.values(THEME_DEFINITIONS).forEach(theme => {
			theme.classes.forEach(className => {
				root.classList.remove(className);
			});
		});

		// Remove all theme CSS variables
		Object.values(THEME_DEFINITIONS).forEach(theme => {
			Object.keys(theme.cssVariables).forEach(variable => {
				root.style.removeProperty(variable);
			});
		});

		// Remove any dynamically loaded theme stylesheets
		const themeLinks = document.head.querySelectorAll('link[data-theme]');
		themeLinks.forEach(link => link.remove());
	}

	private applyThemeConfig(config: ThemeConfig): void {
		if (typeof document === 'undefined') return;

		const root = document.documentElement;

		// Apply CSS variables
		Object.entries(config.cssVariables).forEach(([variable, value]) => {
			root.style.setProperty(variable, value);
		});

		// Apply theme classes
		config.classes.forEach(className => {
			root.classList.add(className);
		});

		// Update meta theme color
		const metaThemeColor = document.querySelector('meta[name="theme-color"]');
		if (metaThemeColor) {
			metaThemeColor.setAttribute('content', config.metaThemeColor);
		}
	}

	public applyTheme(themeName: string): void {
		this.currentTheme = themeName;
		
		// Clear all existing theme styles
		this.clearAllThemeClasses();

		// Resolve the actual theme to apply
		const resolvedTheme = this.resolveTheme(themeName);
		const themeConfig = THEME_DEFINITIONS[resolvedTheme];

		if (!themeConfig) {
			console.warn(`Theme "${resolvedTheme}" not found, falling back to dark theme`);
			this.applyThemeConfig(THEME_DEFINITIONS.dark);
			return;
		}

		// Apply the theme configuration
		this.applyThemeConfig(themeConfig);

		// Store theme preference
		if (typeof localStorage !== 'undefined') {
			localStorage.setItem('theme', themeName);
		}

		// Trigger custom theme application if available
		if (typeof window !== 'undefined' && (window as any).applyTheme) {
			(window as any).applyTheme();
		}
	}

	public getCurrentTheme(): string {
		return this.currentTheme;
	}

	public getAvailableThemes(): Array<{ name: string; displayName: string }> {
		return Object.values(THEME_DEFINITIONS).map(theme => ({
			name: theme.name,
			displayName: theme.displayName
		}));
	}

	public addCustomTheme(config: ThemeConfig): void {
		THEME_DEFINITIONS[config.name] = config;
	}

	public removeCustomTheme(themeName: string): void {
		if (THEME_DEFINITIONS[themeName] && !['light', 'dark', 'system'].includes(themeName)) {
			delete THEME_DEFINITIONS[themeName];
		}
	}

	public initializeTheme(): void {
		if (typeof localStorage !== 'undefined') {
			const savedTheme = localStorage.getItem('theme') || 'system';
			this.applyTheme(savedTheme);
		} else {
			this.applyTheme('system');
		}
	}
}

// Export singleton instance
export const themeManager = ThemeManager.getInstance();
