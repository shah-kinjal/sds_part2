<script lang="ts">
    import { onMount } from "svelte";
    import Sidebar from "$lib/components/Layout/Sidebar.svelte";
    import ChatContainer from "$lib/components/Chat/ChatContainerNew.svelte";
    import PreferencesForm from "$lib/components/Preferences/PreferencesForm.svelte";
    import PropertySuggestions from "$lib/components/Suggestions/PropertySuggestions.svelte";
    import { appState } from "$lib/state.svelte";
    import { getUserPreferences, getPropertySuggestions } from "$lib/api";
    import type { PropertySuggestion } from "$lib/types";

    // View state
    let currentView = $state<'chat' | 'suggestions'>('chat');
    
    // Property suggestions state
    let propertySuggestions = $state<PropertySuggestion[]>([]);
    let hasPreferences = $state(false);
    let isLoadingSuggestions = $state(false);
    let showPreferencesForm = $state(false);
    let errorMessage = $state("");
    let isInitialLoad = $state(true);
    let lastLoadAttempt = $state(0);

    // Remove reactive $effect to prevent loops
    // Load only on explicit user actions (view change, refresh, etc.)
    
    onMount(() => {
        // Initial load if needed
        if (appState.isAuthenticated && currentView === 'suggestions') {
            loadPropertySuggestions();
        }
    });

    function handleViewChange(view: 'chat' | 'suggestions') {
        const wasOnDifferentView = currentView !== view;
        currentView = view;
        
        // Only load if switching TO suggestions view (not already on it)
        if (wasOnDifferentView && view === 'suggestions' && appState.isAuthenticated) {
            loadPropertySuggestions();
        }
    }

    async function loadPropertySuggestions() {
        console.log("=== loadPropertySuggestions called ===");
        console.log("appState.isAuthenticated:", appState.isAuthenticated);
        console.log("isLoadingSuggestions:", isLoadingSuggestions);
        console.log("lastLoadAttempt:", lastLoadAttempt);
        
        // Prevent multiple simultaneous calls
        if (isLoadingSuggestions) {
            console.log("⚠️ Already loading, skipping duplicate call");
            return;
        }
        
        // Prevent calls within 10 seconds of last attempt (anti-spam protection)
        const now = Date.now();
        const timeSinceLastLoad = now - lastLoadAttempt;
        if (lastLoadAttempt > 0 && timeSinceLastLoad < 10000) {
            console.log(`⚠️ Too soon since last load (${Math.round(timeSinceLastLoad/1000)}s ago). Minimum 10 seconds between loads.`);
            return;
        }
        
        if (!appState.isAuthenticated) {
            console.log("❌ Not authenticated, skipping suggestions load");
            return;
        }

        // Update last load attempt time
        lastLoadAttempt = now;
        
        console.log("=== Starting to load property suggestions ===");
        isLoadingSuggestions = true;
        errorMessage = "";
        
        try {
            const response = await getPropertySuggestions(5);
            console.log("Property suggestions response:", response);
            
            if (response.hasPreferences) {
                hasPreferences = true;
                propertySuggestions = response.suggestions || [];
                showPreferencesForm = false; // Make sure form is hidden
                isInitialLoad = false;
                console.log(`✓ Loaded ${propertySuggestions.length} suggestions`);
            } else {
                // No preferences - show form
                hasPreferences = false;
                propertySuggestions = [];
                showPreferencesForm = true;
                isInitialLoad = false;
                console.log("No preferences found, showing form");
            }
        } catch (e: any) {
            console.error("Failed to load property suggestions:", e);
            console.error("Error details:", e.message, e.stack);
            
            // Check if it's an authentication error
            if (e.message && e.message.includes("401")) {
                console.error("❌ Authentication failed - token may be invalid or expired");
                errorMessage = "Authentication failed. Please sign out and sign in again.";
                // Don't show form on auth error - let user know they need to re-authenticate
                showPreferencesForm = false;
            } else {
                // On other errors, show form so user can try setting preferences
                hasPreferences = false;
                propertySuggestions = [];
                showPreferencesForm = true;
            }
            isInitialLoad = false;
        } finally {
            isLoadingSuggestions = false;
            console.log("=== Load complete. hasPreferences:", hasPreferences, "showForm:", showPreferencesForm, "suggestions:", propertySuggestions.length);
        }
    }

    function handlePreferencesSaved() {
        console.log("=== Preferences Saved - Loading Suggestions ===");
        showPreferencesForm = false;
        hasPreferences = true; // Set to true immediately
        loadPropertySuggestions();
    }

    function handleRefreshSuggestions() {
        loadPropertySuggestions();
    }

    function handleEditPreferences() {
        showPreferencesForm = true;
    }

    function handleCancelEdit() {
        showPreferencesForm = false;
    }

    async function handleSignOut() {
        console.log("=== Sign Out Clicked ===");
        try {
            await appState.signOut();
            currentView = 'chat';
            propertySuggestions = [];
            hasPreferences = false;
            showPreferencesForm = false;
            errorMessage = "";
            console.log("✓ Sign out successful");
        } catch (e) {
            console.error("❌ Sign out failed:", e);
        }
    }
</script>

<div class="flex h-screen bg-[var(--bg-body)] overflow-hidden">
        <!-- Left Sidebar -->
        <Sidebar {currentView} onViewChange={handleViewChange}>
            <svelte:fragment slot="footer">
                {#if appState.isAuthenticated}
                    <button
                        onclick={handleSignOut}
                        class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-all text-sm font-medium"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                        </svg>
                        <span>Sign Out</span>
                    </button>
                {:else}
                    <button
                        onclick={() => appState.openLoginModal()}
                        class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white font-semibold hover:shadow-lg transition-all"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
                        </svg>
                        <span>Sign In</span>
                    </button>
                {/if}
            </svelte:fragment>
        </Sidebar>

        <!-- Main Content Area (Center) -->
        <main class="flex-1 overflow-hidden">
        {#if currentView === 'chat'}
            <ChatContainer />
        {:else}
            <!-- Property Suggestions View (Centered) -->
            <div class="h-full flex flex-col items-center bg-[var(--bg-body)] overflow-hidden">
                {#if !appState.isAuthenticated}
                    <!-- Login prompt -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center max-w-md px-6">
                            <div class="mb-6">
                                <svg class="w-20 h-20 mx-auto text-[var(--color-accent-primary)] opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                                </svg>
                            </div>
                            <h2 class="text-2xl font-semibold text-[var(--text-primary)] mb-3">
                                Sign in to view property suggestions
                            </h2>
                            <p class="text-[var(--text-secondary)] mb-8">
                                Get personalized property recommendations based on your preferences.
                            </p>
                            <button
                                onclick={() => (appState.isLoginModalOpen = true)}
                                class="px-6 py-3 rounded-lg font-semibold bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-secondary)] transition-colors"
                            >
                                Sign In
                            </button>
                        </div>
                    </div>
                {:else if isLoadingSuggestions}
                    <!-- Loading State -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center">
                            <div class="flex gap-2 justify-center mb-4">
                                <span class="w-3 h-3 bg-[var(--color-accent-primary)] rounded-full animate-bounce"></span>
                                <span class="w-3 h-3 bg-[var(--color-accent-primary)] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                                <span class="w-3 h-3 bg-[var(--color-accent-primary)] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                            </div>
                            <p class="text-[var(--text-secondary)]">
                                Loading your property suggestions...
                            </p>
                        </div>
                    </div>
                {:else if showPreferencesForm}
                    <!-- Preferences Form (Centered) -->
                    <div class="flex-1 overflow-y-auto w-full">
                        <div class="max-w-2xl mx-auto px-6 py-12">
                            <div class="mb-8 text-center">
                                <h2 class="text-3xl font-semibold text-[var(--text-primary)] mb-3">
                                    {hasPreferences ? "Update Your Preferences" : "Set Your Preferences"}
                                </h2>
                                <p class="text-[var(--text-secondary)]">
                                    {hasPreferences 
                                        ? "Adjust your search criteria to refine your property suggestions."
                                        : "Tell us what you're looking for to get personalized property recommendations."}
                                </p>
                            </div>
                            
                            {#if errorMessage}
                                <div class="mb-6 bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-lg text-sm">
                                    {errorMessage}
                                </div>
                            {/if}
                            
                            <PreferencesForm 
                                onSave={handlePreferencesSaved}
                                onCancel={hasPreferences ? handleCancelEdit : undefined}
                            />
                        </div>
                    </div>
                {:else if hasPreferences}
                    <!-- Property Suggestions Component (Centered) -->
                    <div class="h-full flex flex-col w-full max-w-5xl mx-auto">
                        <div class="border-b border-[var(--border-light)] px-6 py-4 bg-white">
                            <div class="flex items-center justify-between">
                                <h2 class="text-xl font-semibold text-[var(--text-primary)]">
                                    Your Property Matches
                                </h2>
                                <button
                                    onclick={handleEditPreferences}
                                    class="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--bg-container)] text-[var(--text-primary)] font-medium hover:bg-[var(--bg-hover)] transition-all border border-[var(--border-light)]"
                                >
                                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                    </svg>
                                    <span>Edit Preferences</span>
                                </button>
                            </div>
                        </div>
                        <PropertySuggestions 
                            suggestions={propertySuggestions}
                            onRefresh={handleRefreshSuggestions}
                            isLoading={isLoadingSuggestions}
                        />
                    </div>
                {:else}
                    <!-- Error State -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center max-w-md px-6">
                            <p class="text-[var(--text-secondary)] mb-6">
                                {errorMessage || "Something went wrong. Please try again."}
                            </p>
                            <button
                                onclick={() => { showPreferencesForm = true; errorMessage = ""; }}
                                class="px-6 py-3 rounded-lg font-semibold bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-secondary)] transition-colors"
                            >
                                Set Preferences
                            </button>
                        </div>
                    </div>
                {/if}
            </div>
        {/if}
    </main>
</div>
