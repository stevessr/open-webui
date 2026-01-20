import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',

					dest: 'wasm'
				}
			]
		})
	],
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	resolve: {
		// Ensure rolldown-vite sees Svelte conditional exports for UI libs.
		conditions: ['svelte', 'browser', 'module', 'import', 'default'],
		mainFields: ['svelte', 'browser', 'module']
	},
	ssr: {
		resolve: {
			// Match client conditions for SSR resolution.
			conditions: ['svelte', 'browser', 'module', 'import', 'default'],
			mainFields: ['svelte', 'browser', 'module']
		}
	},
	build: {
		sourcemap: true
	},
	worker: {
		format: 'es'
	},
	esbuild: {
		pure: process.env.ENV === 'dev' ? [] : ['console.log', 'console.debug', 'console.error']
	}
});
