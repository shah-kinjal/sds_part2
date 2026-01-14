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

{#snippet footerContent()}
    {#if appState.isAuthenticated}
        <!-- User info row -->
        <div class="flex items-center gap-2 px-2.5 py-1.5 mb-1 rounded-md cursor-pointer">
            <div class="w-6 h-6 rounded-full bg-[var(--sidebar-active)] flex items-center justify-center text-[var(--sidebar-text)] text-xs font-medium">
                {appState.user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <span class="text-xs text-[var(--sidebar-text)] truncate flex-1">
                {appState.user?.email || 'User'}
            </span>
        </div>
        <button
            onclick={handleSignOut}
            class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[var(--sidebar-text-muted)] text-xs"
        >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
            <span>Sign Out</span>
        </button>
    {:else}
        <button
            onclick={() => appState.openLoginModal()}
            class="w-full flex items-center gap-2 px-2.5 py-2 rounded-md text-[var(--sidebar-text)] text-sm"
        >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
            </svg>
            <span>Sign In</span>
        </button>
    {/if}
{/snippet}

<div class="flex h-screen bg-[var(--bg-body)] overflow-hidden">
        <!-- Left Sidebar - Always visible -->
        <Sidebar {currentView} onViewChange={handleViewChange} footer={footerContent} />

        <!-- Main Content Area (Center) -->
        <main class="flex-1 overflow-hidden w-full">
        {#if currentView === 'chat'}
            <ChatContainer />
        {:else}
            <!-- Property Suggestions View (Centered) -->
            <div class="h-full flex flex-col items-center bg-[var(--bg-body)] overflow-hidden">
                {#if !appState.isAuthenticated}
                    <!-- Login prompt -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center max-w-sm px-4">
                            <div class="mb-4">
                                <div class="w-12 h-12 rounded-lg bg-black flex items-center justify-center mx-auto">
                                    <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                                    </svg>
                                </div>
                            </div>
                            <h2 class="text-xl font-semibold text-[var(--text-primary)] mb-2">
                                Sign in for property suggestions
                            </h2>
                            <p class="text-sm text-[var(--text-secondary)] mb-6">
                                Get personalized property recommendations
                            </p>
                            <button
                                onclick={() => (appState.isLoginModalOpen = true)}
                                class="px-5 py-2 rounded-lg text-sm font-medium bg-black text-white hover:bg-gray-800 transition-colors"
                            >
                                Sign In
                            </button>
                        </div>
                    </div>
                {:else if isLoadingSuggestions}
                    <!-- Loading State -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center">
                            <div class="flex gap-1.5 justify-center mb-3">
                                <span class="w-2 h-2 bg-black rounded-full animate-bounce"></span>
                                <span class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.2s]"></span>
                                <span class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.4s]"></span>
                            </div>
                            <p class="text-sm text-[var(--text-secondary)]">
                                Loading suggestions...
                            </p>
                        </div>
                    </div>
                {:else if showPreferencesForm}
                    <!-- Preferences Form (Centered) -->
                    <div class="flex-1 overflow-y-auto w-full">
                        <div class="max-w-2xl mx-auto px-4 py-8 sm:px-6 sm:py-12">
                            <div class="mb-6 text-center">
                                <h2 class="text-2xl font-semibold text-[var(--text-primary)] mb-2">
                                    {hasPreferences ? "Update Preferences" : "Set Preferences"}
                                </h2>
                                <p class="text-sm text-[var(--text-secondary)]">
                                    {hasPreferences
                                        ? "Adjust your search criteria"
                                        : "Tell us what you're looking for"}
                                </p>
                            </div>

                            {#if errorMessage}
                                <div class="mb-4 bg-red-50 border border-red-300 text-red-700 px-3 py-2 rounded-md text-xs">
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
                    <PropertySuggestions
                        suggestions={propertySuggestions}
                        onRefresh={handleRefreshSuggestions}
                        isLoading={isLoadingSuggestions}
                    />
                {:else}
                    <!-- Error State -->
                    <div class="flex-1 flex items-center justify-center w-full">
                        <div class="text-center max-w-sm px-4">
                            <p class="text-sm text-[var(--text-secondary)] mb-4">
                                {errorMessage || "Something went wrong. Please try again."}
                            </p>
                            <button
                                onclick={() => { showPreferencesForm = true; errorMessage = ""; }}
                                class="px-5 py-2 rounded-lg text-sm font-medium bg-black text-white hover:bg-gray-800 transition-colors"
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
