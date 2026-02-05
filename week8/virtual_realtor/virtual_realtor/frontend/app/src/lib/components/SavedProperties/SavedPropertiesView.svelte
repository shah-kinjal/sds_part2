<script lang="ts">
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";
    import { Loader2 } from "lucide-svelte";
    import PropertyCard from "$lib/components/Properties/PropertyCard.svelte";
    import EmptyState from "$lib/components/Properties/EmptyState.svelte";
    import {
        getSavedProperties,
        deleteProperty,
        toggleVisitFlag,
    } from "$lib/api/favorites";
    import { getAuthHeader } from "$lib/auth";
    import type { SavedProperty } from "$lib/types/favorites";

    interface Props {
        visitOnly?: boolean;
    }

    let { visitOnly = false }: Props = $props();

    let properties = $state<SavedProperty[]>([]);
    let isLoading = $state(true);
    let error = $state<string | null>(null);

    async function loadProperties() {
        try {
            isLoading = true;
            error = null;
            const headers = await getAuthHeader();
            const items = await getSavedProperties(visitOnly, headers);
            // Map property_id to id for PropertyCard compatibility
            properties = items.map((p) => ({
                ...p,
                id: p.property_id, // Ensure PropertyData interface satisfaction
            }));
        } catch (e) {
            console.error("Error loading properties:", e);
            error =
                e instanceof Error ? e.message : "Failed to load properties";
        } finally {
            isLoading = false;
        }
    }

    async function handleRemove(id: string) {
        try {
            const headers = await getAuthHeader();
            if (visitOnly) {
                // Should we remove from visit list or favorites?
                // Step 2.5 says remove_property_from_visit_list removes from visit list only.
                // Step 2.4 says remove_property_from_favorites removes completely.
                // In Visit List view, "Remove" implies removing from visit list.
                await toggleVisitFlag(id, false, headers);
                // Remove from local list
                properties = properties.filter((p) => p.property_id !== id);
                // Optionally dispatch event to refresh counts global context if exists
            } else {
                // In Favorites view, "Remove" implies remove from favorites completely
                await deleteProperty(id, headers);
                properties = properties.filter((p) => p.property_id !== id);
            }
        } catch (e) {
            console.error("Error removing property:", e);
            // Optionally show toast
        }
    }

    async function handleAddToVisit(id: string) {
        try {
            const headers = await getAuthHeader();
            const result = await toggleVisitFlag(id, true, headers);
            // Update local state
            const index = properties.findIndex((p) => p.property_id === id);
            if (index !== -1) {
                properties[index] = {
                    ...properties[index],
                    is_visit_candidate: true,
                };
            }
        } catch (e) {
            console.error("Error adding to visit list:", e);
        }
    }

    onMount(() => {
        loadProperties();
    });
</script>

<div class="container mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-8">
        <h1 class="text-3xl font-bold text-gray-900">
            {visitOnly ? "Visit List" : "Saved Properties"}
        </h1>
        <span class="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {properties.length} properties
        </span>
    </div>

    {#if error}
        <div class="bg-red-50 text-red-600 p-4 rounded-lg mb-6">
            <p>{error}</p>
            <button
                onclick={loadProperties}
                class="text-sm font-semibold underline mt-2 hover:text-red-800"
            >
                Try again
            </button>
        </div>
    {/if}

    {#if isLoading}
        <div class="flex justify-center items-center h-64">
            <Loader2 class="w-8 h-8 animate-spin text-indigo-600" />
        </div>
    {:else if properties.length === 0}
        <EmptyState
            message={visitOnly
                ? "Your visit list is empty"
                : "No saved properties yet"}
        />
    {:else}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each properties as property (property.property_id)}
                <div transition:fade|local>
                    <PropertyCard
                        {property}
                        isSaved={true}
                        isInVisitList={property.is_visit_candidate}
                        onRemove={handleRemove}
                        onAddToVisit={!visitOnly && !property.is_visit_candidate
                            ? handleAddToVisit
                            : undefined}
                    />
                </div>
            {/each}
        </div>
    {/if}
</div>
