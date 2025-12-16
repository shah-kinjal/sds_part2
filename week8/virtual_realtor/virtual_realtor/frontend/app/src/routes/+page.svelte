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

    onMount(() => {
        if (appState.isAuthenticated && currentView === 'suggestions') {
            loadPropertySuggestions();
        }
    });

    $effect(() => {
        // Only trigger if authenticated and on suggestions view
        // Prevent loops by checking if we're already loading or just loaded
        const now = Date.now();
        const timeSinceLastLoad = now - lastLoadAttempt;
        
        if (appState.isAuthenticated && currentView === 'suggestions' && !isLoadingSuggestions && timeSinceLastLoad > 1000) {
            // Only load if not already loading and at least 1 second since last attempt
            loadPropertySuggestions();
        } else if (!appState.isAuthenticated) {
            propertySuggestions = [];
            hasPreferences = false;
            showPreferencesForm = false;
            errorMessage = "";
            isInitialLoad = true;
        }
    });

    function handleViewChange(view: 'chat' | 'suggestions') {
        currentView = view;
        if (view === 'suggestions' && appState.isAuthenticated) {
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
        
        if (!appState.isAuthenticated) {
            console.log("❌ Not authenticated, skipping suggestions load");
            return;
        }

        // Update last load attempt time
        lastLoadAttempt = Date.now();
        
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
                    class="w-full px-4 py-2.5 rounded-lg text-[var(--text-primary)] hover:bg-[var(--bg-container)] transition-colors text-sm font-medium text-left"
                >
                    Sign Out
                </button>
            {:else}
                <button
                    onclick={() => {
                        console.log("=== Sign In Button Clicked ===");
                        console.log("Before - appState.isLoginModalOpen:", appState.isLoginModalOpen);
                        appState.openLoginModal();
                        console.log("After - appState.isLoginModalOpen:", appState.isLoginModalOpen);
                    }}
                    class="w-full px-4 py-2.5 rounded-lg bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-secondary)] transition-colors text-sm font-medium"
                >
                    Sign In
                </button>
            {/if}
        </svelte:fragment>
    </Sidebar>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden">
        {#if currentView === 'chat'}
            <ChatContainer />
        {:else}
            <!-- Property Suggestions View -->
            <div class="h-full flex flex-col bg-[var(--bg-body)]">
                {#if !appState.isAuthenticated}
                    <!-- Login prompt -->
                    <div class="flex-1 flex items-center justify-center">
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
                    <div class="flex-1 flex items-center justify-center">
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
                    <!-- Preferences Form -->
                    <div class="flex-1 overflow-y-auto">
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
                    <!-- Property Suggestions -->
                    <div class="flex-1 overflow-y-auto">
                        <div class="max-w-4xl mx-auto px-6 py-8">
                            <div class="mb-6 flex justify-between items-center">
                                <div>
                                    <h2 class="text-2xl font-semibold text-[var(--text-primary)] mb-1">
                                        Property Suggestions
                                    </h2>
                                    <p class="text-[var(--text-secondary)] text-sm">
                                        {propertySuggestions.length} {propertySuggestions.length === 1 ? 'property' : 'properties'} found based on your preferences
                                    </p>
                                </div>
                                <div class="flex gap-2">
                                    <button
                                        onclick={handleEditPreferences}
                                        class="px-4 py-2 rounded-lg border border-[var(--color-border-primary)] text-[var(--text-primary)] hover:bg-[var(--bg-container)] transition-colors text-sm font-medium"
                                    >
                                        ✏️ Edit Preferences
                                    </button>
                                    <button
                                        onclick={handleRefreshSuggestions}
                                        class="px-4 py-2 rounded-lg bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-secondary)] transition-colors text-sm font-medium"
                                    >
                                        🔄 Refresh
                                    </button>
                                </div>
                            </div>

                            <!-- Properties List -->
                            <div class="space-y-4">
                                {#each propertySuggestions as property, index}
                                    <div class="bg-[var(--bg-card)] border border-[var(--color-border-primary)] rounded-xl p-6 hover:border-[var(--color-accent-primary)] transition-all shadow-sm hover:shadow-md">
                                        <div class="flex items-start gap-4">
                                            <div class="flex-shrink-0 w-10 h-10 rounded-full bg-[var(--color-accent-primary)] flex items-center justify-center text-white font-bold">
                                                {index + 1}
                                            </div>
                                            
                                            <div class="flex-1">
                                                <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">
                                                    {property.address}
                                                </h3>

                                                <div class="text-2xl font-bold text-[var(--color-accent-primary)] mb-4">
                                                    {new Intl.NumberFormat("en-US", {
                                                        style: "currency",
                                                        currency: "USD",
                                                        maximumFractionDigits: 0,
                                                    }).format(property.price)}
                                                </div>

                                                <div class="grid grid-cols-2 gap-3 mb-4">
                                                    <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                                                        <span class="text-xl">🛏️</span>
                                                        <span class="font-semibold text-[var(--text-primary)]">{property.beds}</span>
                                                        <span>bed{property.beds !== 1 ? 's' : ''}</span>
                                                    </div>
                                                    <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                                                        <span class="text-xl">🛁</span>
                                                        <span class="font-semibold text-[var(--text-primary)]">{property.baths}</span>
                                                        <span>bath{property.baths !== 1 ? 's' : ''}</span>
                                                    </div>
                                                    <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                                                        <span class="text-xl">📏</span>
                                                        <span class="font-semibold text-[var(--text-primary)]">{property.sqft.toLocaleString()}</span>
                                                        <span>sqft</span>
                                                    </div>
                                                    <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                                                        <span class="text-xl">📅</span>
                                                        <span class="font-semibold text-[var(--text-primary)]">{property.daysOnMarket}</span>
                                                        <span>day{property.daysOnMarket !== 1 ? 's' : ''}</span>
                                                    </div>
                                                </div>

                                                <a
                                                    href={property.sourceUrl}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-secondary)] transition-colors text-sm font-medium"
                                                >
                                                    <span>View on Zillow</span>
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
                                                    </svg>
                                                </a>
                                            </div>
                                        </div>
                                    </div>
                                {/each}
                            </div>
                        </div>
                    </div>
                {:else}
                    <!-- Error State -->
                    <div class="flex-1 flex items-center justify-center">
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
