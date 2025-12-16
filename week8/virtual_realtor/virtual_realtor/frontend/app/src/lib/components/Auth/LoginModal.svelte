<script lang="ts">
    import {
        startPasswordlessSignIn,
        completePasswordlessSignIn,
    } from "$lib/auth";
    import { appState } from "$lib/state.svelte";

    let { isOpen, onClose, onLogin } = $props();
    
    // Debug logging
    $effect(() => {
        console.log("LoginModal isOpen prop changed:", isOpen);
        console.log("LoginModal component will render:", isOpen ? "YES" : "NO");
    });

    let email = $state("");
    let otp = $state("");
    let step = $state<"EMAIL" | "OTP">("EMAIL");
    let isLoading = $state(false);
    let errorMessage = $state("");

    async function handleSubmit(e: Event) {
        e.preventDefault();
        console.log("=== Login Form Submitted ===", { step, email: email ? "present" : "missing" });
        errorMessage = "";
        isLoading = true;

        try {
            if (step === "EMAIL") {
                console.log("Sending OTP to:", email);
                const needsOtp = await startPasswordlessSignIn(email);
                console.log("OTP needed:", needsOtp);
                if (needsOtp) {
                    step = "OTP";
                    console.log("Switched to OTP step");
                } else {
                    console.log("No OTP needed?");
                }
            } else {
                console.log("Verifying OTP...");
                const success = await completePasswordlessSignIn(otp);
                console.log("OTP verification result:", success);
                if (success) {
                    appState.setAuthenticated(true);
                    console.log("✓ Authentication successful!");
                    onLogin(email);
                    onCloseInternal();
                } else {
                    errorMessage = "Failed to verify OTP";
                    console.error("❌ OTP verification failed");
                }
            }
        } catch (err) {
            console.error("❌ Login error:", err);
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
    <!-- Ultra-simple test overlay -->
    <div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); z-index: 999999; display: flex; align-items: center; justify-content: center; font-family: Arial;">
        <div style="background: white; padding: 40px; border-radius: 10px; text-align: center; max-width: 400px; box-shadow: 0 20px 60px rgba(0,0,0,0.5);">
            <h1 style="color: black; font-size: 24px; margin-bottom: 20px;">Sign In</h1>
            
            {#if step === "EMAIL"}
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: black; margin-bottom: 8px; text-align: left; font-weight: bold;">Email Address</label>
                    <input
                        type="email"
                        bind:value={email}
                        placeholder="Enter your email"
                        style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; box-sizing: border-box;"
                        required
                        disabled={isLoading}
                    />
                </div>
                
                <button
                    onclick={(e) => { e.preventDefault(); handleSubmit(e); }}
                    style="width: 100%; padding: 12px; background: black; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-bottom: 10px;"
                    disabled={isLoading}
                >
                    {isLoading ? "Processing..." : "Send OTP"}
                </button>
            {:else}
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: black; margin-bottom: 8px; text-align: left; font-weight: bold;">One-Time Password</label>
                    <input
                        type="text"
                        bind:value={otp}
                        placeholder="Enter code from email"
                        style="width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; box-sizing: border-box;"
                        required
                        disabled={isLoading}
                    />
                    <p style="color: #666; font-size: 12px; margin-top: 5px; text-align: left;">Check your email for the code.</p>
                </div>
                
                <button
                    onclick={(e) => { e.preventDefault(); handleSubmit(e); }}
                    style="width: 100%; padding: 12px; background: black; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: bold; cursor: pointer; margin-bottom: 10px;"
                    disabled={isLoading}
                >
                    {isLoading ? "Processing..." : "Verify & Login"}
                </button>
                
                <button
                    onclick={() => (step = "EMAIL")}
                    style="width: 100%; padding: 12px; background: #f5f5f5; color: black; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; cursor: pointer;"
                    disabled={isLoading}
                >
                    Back
                </button>
            {/if}
            
            {#if errorMessage}
                <div style="background: #fee; border: 1px solid #fcc; color: #c00; padding: 10px; border-radius: 6px; margin-top: 15px; font-size: 14px;">
                    {errorMessage}
                </div>
            {/if}
            
            <button
                onclick={onCloseInternal}
                style="position: absolute; top: 10px; right: 10px; background: transparent; border: none; font-size: 30px; color: #999; cursor: pointer; line-height: 1; width: 40px; height: 40px;"
            >&times;</button>
        </div>
    </div>
{:else}
    <div style="display: none;">Modal closed (isOpen={isOpen})</div>
{/if}
