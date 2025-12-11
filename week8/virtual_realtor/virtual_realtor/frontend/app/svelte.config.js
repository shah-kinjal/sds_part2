import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://svelte.dev/docs/kit/integrations
	// for more information about preprocessors
	preprocess: vitePreprocess(),

	kit: {
		// adapter-static config context for SPA
		adapter: adapter({
			fallback: 'index.html' // Important for SPA behavior on S3/CloudFront with rewrites
		})
	}
};

export default config;
