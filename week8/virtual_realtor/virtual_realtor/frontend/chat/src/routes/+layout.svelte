<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { signOutUser } from '$lib/auth';
	import { goto } from '$app/navigation';
	import { LogOut } from 'lucide-svelte';

	let { data, children } = $props();

	async function handleSignOut() {
		await signOutUser();
		await goto('/login');
	}
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="preconnect" href="https://fonts.googleapis.com">
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
	<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
</svelte:head>

<div class="font-sans antialiased" style="font-family: 'Inter', sans-serif;">
	{#if data.isAuthenticated}
		<header class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-sm">
			<div class="mx-auto max-w-7xl px-6 py-3 flex items-center justify-between">
				<a href="/" class="flex items-center gap-2 text-lg font-semibold text-slate-900 hover:text-pink-600 transition-colors">
					<svg class="w-8 h-8" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
						<rect x="30" y="50" width="40" height="35" fill="#88d8a3" opacity="0.8"/>
						<path d="M 20 50 L 50 25 L 80 50 Z" fill="#ff8b94" opacity="0.9"/>
						<rect x="42" y="65" width="16" height="20" fill="#2d3436" opacity="0.7"/>
						<rect x="33" y="55" width="10" height="10" fill="#a8e6cf" opacity="0.9"/>
						<rect x="57" y="55" width="10" height="10" fill="#a8e6cf" opacity="0.9"/>
						<circle cx="55" cy="75" r="1.5" fill="#ff8b94"/>
					</svg>
					Virtual Realtor
				</a>
				<button
					onclick={handleSignOut}
					type="button"
					class="inline-flex items-center gap-2 rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-700 transition-all duration-200 hover:bg-slate-200 hover:scale-105"
				>
					<LogOut class="h-4 w-4" />
					Sign Out
				</button>
			</div>
		</header>
		<div class="pt-16">
			{@render children()}
		</div>
	{:else}
		{@render children()}
	{/if}
</div>

