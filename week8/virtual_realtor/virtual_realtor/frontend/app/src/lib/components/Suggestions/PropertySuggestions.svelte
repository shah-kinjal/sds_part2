<script lang="ts">
    import type { PropertySuggestion } from "$lib/types";

    let { suggestions, onRefresh, isLoading = false } = $props<{
        suggestions: PropertySuggestion[];
        onRefresh: () => void;
        isLoading?: boolean;
    }>();

    function formatPrice(price: number): string {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0,
        }).format(price);
    }
</script>

<div class="h-full flex flex-col">
    {#if isLoading}
        <div class="flex-1 flex items-center justify-center py-12">
            <div class="text-center">
                <div class="flex gap-2 justify-center mb-3">
                    <span class="w-3 h-3 bg-[var(--typing-dot)] rounded-full animate-bounce"></span>
                    <span class="w-3 h-3 bg-[var(--typing-dot)] rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span class="w-3 h-3 bg-[var(--typing-dot)] rounded-full animate-bounce [animation-delay:0.4s]"></span>
                </div>
                <p class="text-sm text-[var(--text-secondary)]">
                    Finding the perfect properties for you...
                </p>
            </div>
        </div>
    {:else if suggestions.length === 0}
        <div class="flex-1 flex items-center justify-center py-12">
            <div class="text-center px-4">
                <svg class="w-16 h-16 mx-auto mb-4 text-[var(--color-accent-primary)] opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                </svg>
                <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">
                    No properties found
                </h3>
                <p class="text-sm text-[var(--text-secondary)] mb-4">
                    Try adjusting your preferences or refresh to see new listings.
                </p>
                <button
                    onclick={onRefresh}
                    class="text-sm px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--color-accent-tertiary)] to-[var(--color-accent-quaternary)] text-white font-medium hover:opacity-90"
                >
                    Try Again
                </button>
            </div>
        </div>
    {:else}
        <!-- Header with count and refresh -->
        <div class="px-6 py-4 border-b-2 border-[var(--color-border-primary)] bg-[var(--bg-suggestions)]">
            <div class="flex justify-between items-center">
                <div>
                    <h3 class="text-base font-bold text-[var(--text-primary)]">
                        {suggestions.length} {suggestions.length === 1 ? 'Property' : 'Properties'} Found
                    </h3>
                    <p class="text-sm text-[var(--text-secondary)] mt-0.5">
                        Based on your preferences
                    </p>
                </div>
                <button
                    onclick={onRefresh}
                    class="text-sm px-4 py-2 rounded-lg bg-gradient-to-br from-[var(--color-accent-tertiary)] to-[var(--color-accent-quaternary)] text-white font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity shadow-sm"
                    disabled={isLoading}
                >
                    🔄 Refresh
                </button>
            </div>
        </div>

        <!-- Properties List -->
        <div class="flex-1 overflow-y-auto p-6 space-y-4">
            {#each suggestions as property, index}
                <div class="bg-white dark:bg-[#262B28] border-2 border-[var(--color-border-primary)] rounded-xl p-5 hover:shadow-xl transition-all duration-200 hover:border-[var(--color-accent-primary)]">
                    <!-- Property Number Badge -->
                    <div class="flex items-start gap-3">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] flex items-center justify-center text-white font-bold text-base shadow-sm">
                            {index + 1}
                        </div>
                        
                        <div class="flex-1 min-w-0">
                            <!-- Address -->
                            <h4 class="text-base font-bold text-[var(--text-primary)] mb-2 leading-tight">
                                {property.address}
                            </h4>

                            <!-- Price -->
                            <div class="text-3xl font-bold text-[var(--color-accent-primary)] mb-4">
                                {formatPrice(property.price)}
                            </div>

                            <!-- Property Details Grid -->
                            <div class="grid grid-cols-2 gap-3 mb-4">
                                <div class="flex items-center gap-2 text-sm">
                                    <span class="text-xl">🛏️</span>
                                    <span class="font-bold text-[var(--text-primary)]">{property.beds}</span>
                                    <span class="text-[var(--text-secondary)] font-medium">bed{property.beds !== 1 ? 's' : ''}</span>
                                </div>
                                <div class="flex items-center gap-2 text-sm">
                                    <span class="text-xl">🛁</span>
                                    <span class="font-bold text-[var(--text-primary)]">{property.baths}</span>
                                    <span class="text-[var(--text-secondary)] font-medium">bath{property.baths !== 1 ? 's' : ''}</span>
                                </div>
                                <div class="flex items-center gap-2 text-sm">
                                    <span class="text-xl">📏</span>
                                    <span class="font-bold text-[var(--text-primary)]">{property.sqft.toLocaleString()}</span>
                                    <span class="text-[var(--text-secondary)] font-medium">sqft</span>
                                </div>
                                <div class="flex items-center gap-2 text-sm">
                                    <span class="text-xl">📅</span>
                                    <span class="font-bold text-[var(--text-primary)]">{property.daysOnMarket}</span>
                                    <span class="text-[var(--text-secondary)] font-medium">day{property.daysOnMarket !== 1 ? 's' : ''}</span>
                                </div>
                            </div>

                            <!-- View on Zillow Button -->
                            <a
                                href={property.sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                class="inline-flex items-center gap-2 text-sm px-5 py-2.5 rounded-lg bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] text-white font-bold hover:opacity-90 transition-opacity shadow-md hover:shadow-lg"
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
    {/if}
</div>
