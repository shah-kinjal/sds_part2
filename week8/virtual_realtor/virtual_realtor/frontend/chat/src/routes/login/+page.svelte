<script lang="ts">
	import { goto } from '$app/navigation';
	import { signInWithPassword } from '$lib/auth';
	import { User, Lock, AlertTriangle, Home, LogIn } from 'lucide-svelte';

	let username = '';
	let password = '';
	let loading = false;
	let error: string | null = null;

	async function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		error = null;
		loading = true;
		try {
			const success = await signInWithPassword(username, password);
			if (success) {
				await goto('/');
			} else {
				error = 'Sign in failed. Please check your credentials.';
			}
		} catch (e: any) {
			error = e.message || 'An unknown error occurred. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Login - Virtual Realtor</title>
</svelte:head>

<div class="min-h-screen gradient-bg flex items-center justify-center p-6 relative overflow-hidden">
	<!-- Background decorations -->
	<div class="absolute inset-0 overflow-hidden">
		<div
			class="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-white/10 blur-3xl animate-float"
		></div>
		<div
			class="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-white/10 blur-3xl animate-float"
			style="animation-delay: -3s;"
		></div>
	</div>

	<div class="relative z-10 w-full max-w-md space-y-8">
		<div class="text-center">
			<div
				class="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-sm shadow-2xl"
			>
				<Home class="h-8 w-8 text-slate-900" />
			</div>
			<h1 class="text-4xl font-bold tracking-tight text-slate-900">
				Virtual Realtor
			</h1>
			<p class="mt-3 text-lg text-slate-800">
				Sign in to start your property search
			</p>
		</div>

		<div
			class="glass-card rounded-2xl p-8 shadow-2xl bg-white/80 backdrop-blur-xl border border-white/20"
		>
			{#if error}
				<div
					class="mb-6 flex items-start space-x-3 rounded-xl border border-red-300 bg-red-50 p-4"
				>
					<AlertTriangle class="h-5 w-5 flex-shrink-0 text-red-600" />
					<div class="flex-1">
						<h3 class="font-semibold text-red-800">Authentication Error</h3>
						<p class="text-sm text-red-700">{error}</p>
					</div>
				</div>
			{/if}

			<form class="space-y-6" onsubmit={handleSubmit}>
				<div>
					<label for="username" class="block text-sm font-semibold text-slate-700 mb-3">
						Username
					</label>
					<div class="relative">
						<User
							class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500"
						/>
						<input
							id="username"
							name="username"
							type="text"
							autocomplete="username"
							required
							bind:value={username}
							class="block w-full rounded-xl border-0 bg-slate-50 py-4 pl-12 pr-4 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 transition-all duration-200 placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-pink-400"
							placeholder="Enter your username"
						/>
					</div>
				</div>

				<div>
					<label for="password" class="block text-sm font-semibold text-slate-700 mb-3">
						Password
					</label>
					<div class="relative">
						<Lock
							class="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-500"
						/>
						<input
							id="password"
							name="password"
							type="password"
							autocomplete="current-password"
							required
							bind:value={password}
							class="block w-full rounded-xl border-0 bg-slate-50 py-4 pl-12 pr-4 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 transition-all duration-200 placeholder:text-slate-400 focus:bg-white focus:ring-2 focus:ring-pink-400"
							placeholder="Enter your password"
						/>
					</div>
				</div>

				<button
					type="submit"
					disabled={loading || !username || !password}
					class="btn-primary w-full py-4 text-base font-semibold disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:scale-100"
				>
					{#if loading}
						<div
							class="h-5 w-5 animate-spin rounded-full border-2 border-slate-900 border-t-transparent"
						></div>
						Signing in...
					{:else}
						<LogIn class="h-5 w-5" />
						Sign In
					{/if}
				</button>
			</form>
		</div>

		<div class="text-center">
			<p class="text-sm text-slate-800">
				Secured with AWS Cognito authentication
			</p>
		</div>
	</div>
</div>

<style>
	@keyframes float {
		0%,
		100% {
			transform: translateY(0px);
		}
		50% {
			transform: translateY(-20px);
		}
	}

	.animate-float {
		animation: float 6s ease-in-out infinite;
	}
</style>

