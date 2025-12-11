<script lang="ts">
    import {
        startPasswordlessSignIn,
        completePasswordlessSignIn,
    } from "$lib/auth";
    import { appState } from "$lib/state.svelte";

    let { isOpen, onClose, onLogin } = $props();

    let email = $state("");
    let otp = $state("");
    let step = $state<"EMAIL" | "OTP">("EMAIL");
    let isLoading = $state(false);
    let errorMessage = $state("");

    async function handleSubmit(e: Event) {
        e.preventDefault();
        errorMessage = "";
        isLoading = true;

        try {
            if (step === "EMAIL") {
                const needsOtp = await startPasswordlessSignIn(email);
                if (needsOtp) {
                    step = "OTP";
                } else {
                    // Should not happen for this flow usually, or maybe direct login?
                    console.log("No OTP needed?");
                }
            } else {
                const success = await completePasswordlessSignIn(otp);
                if (success) {
                    appState.setAuthenticated(true);
                    onLogin(email);
                    onCloseInternal();
                } else {
                    errorMessage = "Failed to verify OTP";
                }
            }
        } catch (err) {
            console.error(err);
            errorMessage = "An error occurred. Please try again.";
        } finally {
            isLoading = false;
        }
    }

    function onCloseInternal() {
        step = "EMAIL";
        email = "";
        otp = "";
        errorMessage = "";
        onClose();
    }
</script>

{#if isOpen}
    <div
        class="fixed inset-0 w-full h-full bg-black/50 z-[1000] flex items-center justify-center"
    >
        <div
            class="bg-white dark:bg-[#252525] p-8 rounded-xl w-[90%] max-w-[400px] shadow-2xl relative border-2 border-[var(--color-border-primary)]"
        >
            <button
                onclick={onCloseInternal}
                class="absolute top-2 right-2 bg-none border-none text-[rgba(45,52,54,0.8)] dark:text-[rgba(224,224,224,0.8)] text-2xl cursor-pointer"
                >&times;</button
            >
            <h2
                class="mb-5 text-[#2d3436] dark:text-[#e0e0e0] text-center text-xl font-bold"
            >
                {step === "EMAIL" ? "Sign In" : "Enter OTP"}
            </h2>

            {#if errorMessage}
                <div
                    class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4 text-sm"
                >
                    {errorMessage}
                </div>
            {/if}

            <form onsubmit={handleSubmit}>
                {#if step === "EMAIL"}
                    <div class="mb-4">
                        <label
                            for="email"
                            class="block mb-2 text-[rgba(45,52,54,0.8)] dark:text-[rgba(224,224,224,0.8)] text-sm"
                            >Email Address</label
                        >
                        <input
                            type="email"
                            id="email"
                            bind:value={email}
                            placeholder="Enter your email"
                            class="w-full p-2.5 border-2 border-[var(--color-border-primary)] rounded-lg bg-white dark:bg-[#2c2c2c] text-[#2d3436] dark:text-[#e0e0e0] text-base"
                            required
                            disabled={isLoading}
                        />
                    </div>
                {:else}
                    <div class="mb-4">
                        <label
                            for="otp"
                            class="block mb-2 text-[rgba(45,52,54,0.8)] dark:text-[rgba(224,224,224,0.8)] text-sm"
                            >One-Time Password</label
                        >
                        <input
                            type="text"
                            id="otp"
                            bind:value={otp}
                            placeholder="Enter verification code"
                            class="w-full p-2.5 border-2 border-[var(--color-border-primary)] rounded-lg bg-white dark:bg-[#2c2c2c] text-[#2d3436] dark:text-[#e0e0e0] text-base"
                            required
                            disabled={isLoading}
                        />
                        <p class="text-xs text-[var(--text-muted)] mt-1">
                            Check your email for the code.
                        </p>
                    </div>
                {/if}

                <div class="flex gap-2 mt-5">
                    <button
                        type="submit"
                        class="flex-1 p-2.5 rounded-lg border-none cursor-pointer font-semibold bg-gradient-to-br from-[var(--color-accent-tertiary)] to-[var(--color-accent-quaternary)] text-white disabled:opacity-50"
                        disabled={isLoading}
                    >
                        {isLoading
                            ? "Processing..."
                            : step === "EMAIL"
                              ? "Send OTP"
                              : "Verify & Login"}
                    </button>
                    {#if step === "OTP"}
                        <button
                            type="button"
                            onclick={() => (step = "EMAIL")}
                            class="p-2.5 rounded-lg border-2 border-[var(--color-border-primary)] bg-transparent text-[var(--text-primary)] cursor-pointer font-semibold"
                            disabled={isLoading}
                        >
                            Back
                        </button>
                    {/if}
                </div>
            </form>
        </div>
    </div>
{/if}
