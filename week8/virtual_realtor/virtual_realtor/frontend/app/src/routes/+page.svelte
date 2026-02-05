<script module>
    import { Building } from "lucide-svelte";
</script>

<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import ChatContainer from "$lib/components/Chat/ChatContainerNew.svelte";
    import PreferencesForm from "$lib/components/Preferences/PreferencesForm.svelte";
    import PropertySuggestions from "$lib/components/Suggestions/PropertySuggestions.svelte";
    import { appState } from "$lib/state.svelte";
    import { getPropertySuggestions } from "$lib/api";
    import type { PropertySuggestion } from "$lib/types";

    // View state derived from URL
    let currentView = $derived(
        $page.url.searchParams.get("view") === "suggestions"
            ? "suggestions"
            : "chat",
    );

    // Property suggestions state
    let propertySuggestions = $state<PropertySuggestion[]>([]);
    let hasPreferences = $state(false);
    let isLoadingSuggestions = $state(false);
    let showPreferencesForm = $state(false);
    let errorMessage = $state("");
    let isInitialLoad = $state(true);
    let lastLoadAttempt = $state(0);

    // Effect to load suggestions when view changes or auth changes
    $effect(() => {
        if (currentView === "suggestions" && appState.isAuthenticated) {
            loadPropertySuggestions();
        }
    });

    onMount(() => {
        // Initial load if needed
        if (appState.isAuthenticated && currentView === "suggestions") {
            loadPropertySuggestions();
        }
    });

    async function loadPropertySuggestions() {
        console.log("=== loadPropertySuggestions called ===");

        // Prevent multiple simultaneous calls
        if (isLoadingSuggestions) {
            return;
        }

        // Prevent spam
        const now = Date.now();
        if (lastLoadAttempt > 0 && now - lastLoadAttempt < 10000) {
            return;
        }

        if (!appState.isAuthenticated) {
            return;
        }

        lastLoadAttempt = now;
        isLoadingSuggestions = true;
        errorMessage = "";

        try {
            const response = await getPropertySuggestions(5);

            if (response.hasPreferences) {
                hasPreferences = true;
                propertySuggestions = response.suggestions || [];
                showPreferencesForm = false;
                isInitialLoad = false;
            } else {
                hasPreferences = false;
                propertySuggestions = [];
                showPreferencesForm = true;
                isInitialLoad = false;
            }
        } catch (e: any) {
            console.error("Failed to load property suggestions:", e);
            if (e.message && e.message.includes("401")) {
                errorMessage =
                    "Authentication failed. Please sign out and sign in again.";
                showPreferencesForm = false;
            } else {
                hasPreferences = false;
                propertySuggestions = [];
                showPreferencesForm = true;
            }
            isInitialLoad = false;
        } finally {
            isLoadingSuggestions = false;
        }
    }

    function handlePreferencesSaved() {
        showPreferencesForm = false;
        hasPreferences = true;
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
</script>

<!-- Main Content Area -->
{#if currentView === "chat"}
    <ChatContainer />
{:else}
    <!-- Property Suggestions View (Centered) -->
    <div
        class="h-full flex flex-col items-center bg-[var(--bg-body)] overflow-hidden"
    >
        {#if !appState.isAuthenticated}
            <!-- Login prompt -->
            <div class="flex-1 flex items-center justify-center w-full">
                <div class="text-center max-w-sm px-4">
                    <div class="mb-4">
                        <div
                            class="w-12 h-12 rounded-lg bg-black flex items-center justify-center mx-auto"
                        >
                            <Building class="w-7 h-7 text-white" />
                        </div>
                    </div>
                    <h2
                        class="text-xl font-semibold text-[var(--text-primary)] mb-2"
                    >
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
                        <span
                            class="w-2 h-2 bg-black rounded-full animate-bounce"
                        ></span>
                        <span
                            class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.2s]"
                        ></span>
                        <span
                            class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.4s]"
                        ></span>
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
                        <h2
                            class="text-2xl font-semibold text-[var(--text-primary)] mb-2"
                        >
                            {hasPreferences
                                ? "Update Preferences"
                                : "Set Preferences"}
                        </h2>
                        <p class="text-sm text-[var(--text-secondary)]">
                            {hasPreferences
                                ? "Adjust your search criteria"
                                : "Tell us what you're looking for"}
                        </p>
                    </div>

                    {#if errorMessage}
                        <div
                            class="mb-4 bg-red-50 border border-red-300 text-red-700 px-3 py-2 rounded-md text-xs"
                        >
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
                        {errorMessage ||
                            "Something went wrong. Please try again."}
                    </p>
                    <button
                        onclick={() => {
                            showPreferencesForm = true;
                            errorMessage = "";
                        }}
                        class="px-5 py-2 rounded-lg text-sm font-medium bg-black text-white hover:bg-gray-800 transition-colors"
                    >
                        Set Preferences
                    </button>
                </div>
            </div>
        {/if}
    </div>
{/if}
