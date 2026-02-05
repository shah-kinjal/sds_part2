<script lang="ts">
	import favicon from "$lib/assets/favicon.svg";
	import "../app.css";
	import { onMount } from "svelte";
	import { checkIsAuthenticated } from "$lib/auth";
	import { appState } from "$lib/state.svelte";
	import LoginModal from "$lib/components/Auth/LoginModal.svelte";
	import Sidebar from "$lib/components/Layout/Sidebar.svelte";

	let { children } = $props();

	onMount(async () => {
		const isAuth = await checkIsAuthenticated();
		appState.setAuthenticated(isAuth);
		console.log("App mounted. Authenticated:", isAuth);
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex h-screen bg-[var(--bg-body)] overflow-hidden">
	<!-- Global Sidebar -->
	<Sidebar footer={footerContent} />

	<!-- Main Content Area -->
	<main class="flex-1 overflow-hidden w-full relative">
		{@render children()}
	</main>
</div>

<!-- Login Modal available globally -->
<LoginModal
	isOpen={appState.isLoginModalOpen}
	onClose={() => {
		console.log("=== Login Modal onClose called ===");
		appState.closeLoginModal();
	}}
	onLogin={(email: string) => {
		console.log("=== Login Successful ===", email);
		appState.closeLoginModal();
	}}
/>

<!-- Snippet for Sidebar Footer -->
{#snippet footerContent()}
	{#if appState.isAuthenticated}
		<!-- User info row -->
		<div
			class="flex items-center gap-2 px-2.5 py-1.5 mb-1 rounded-md cursor-pointer"
		>
			<div
				class="w-6 h-6 rounded-full bg-[var(--sidebar-active)] flex items-center justify-center text-[var(--sidebar-text)] text-xs font-medium"
			>
				{appState.user?.email?.charAt(0).toUpperCase() || "U"}
			</div>
			<span class="text-xs text-[var(--sidebar-text)] truncate flex-1">
				{appState.user?.email || "User"}
			</span>
		</div>
		<button
			onclick={async () => await appState.signOut()}
			class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[var(--sidebar-text-muted)] text-xs hover:text-[var(--sidebar-text)]"
		>
			<svg
				class="w-3.5 h-3.5"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
				/>
			</svg>
			<span>Sign Out</span>
		</button>
	{:else}
		<button
			onclick={() => appState.openLoginModal()}
			class="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[var(--sidebar-text)] text-sm hover:bg-[var(--sidebar-hover)]"
		>
			<svg
				class="w-4 h-4"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
				/>
			</svg>
			<span>Sign In</span>
		</button>
	{/if}
{/snippet}
