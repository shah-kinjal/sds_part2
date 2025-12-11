<script lang="ts">
	import favicon from "$lib/assets/favicon.svg";
	import "../app.css";
	import { onMount } from "svelte";
	import { checkIsAuthenticated } from "$lib/auth";
	import { appState } from "$lib/state.svelte";
	import LoginModal from "$lib/components/Auth/LoginModal.svelte";

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

{@render children()}

<LoginModal
	isOpen={appState.isLoginModalOpen}
	onClose={() => (appState.isLoginModalOpen = false)}
	onLogin={(email: string) => console.log("Login requested", email)}
/>
