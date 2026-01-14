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

    function formatNumber(num: number): string {
        return new Intl.NumberFormat("en-US").format(num);
    }
</script>

<div class="h-full flex flex-col bg-[var(--bg-body)] overflow-hidden">
    <div class="flex-1 overflow-y-auto">
        <div class="max-w-[48rem] mx-auto px-3 py-4 sm:px-4 sm:py-6">
            {#if isLoading}
                <!-- Loading State -->
                <div class="flex items-center justify-center py-12">
                    <div class="text-center">
                        <div class="flex gap-1.5 justify-center mb-3">
                            <span class="w-2 h-2 bg-black rounded-full animate-bounce"></span>
                            <span class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.2s]"></span>
                            <span class="w-2 h-2 bg-black rounded-full animate-bounce [animation-delay:0.4s]"></span>
                        </div>
                        <p class="text-sm text-[var(--text-secondary)]">
                            Finding properties...
                        </p>
                    </div>
                </div>
            {:else if suggestions.length === 0}
                <!-- Empty State -->
                <div class="flex items-center justify-center py-12">
                    <div class="text-center max-w-sm">
                        <div class="mb-4">
                            <div class="w-12 h-12 rounded-lg bg-black flex items-center justify-center mx-auto">
                                <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                                </svg>
                            </div>
                        </div>
                        <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">
                            No Properties Found
                        </h3>
                        <p class="text-sm text-[var(--text-secondary)] mb-4">
                            Try adjusting your preferences or refresh for new listings
                        </p>
                        <button
                            onclick={onRefresh}
                            class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-black text-white text-sm font-medium"
                        >
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                            </svg>
                            <span>Refresh</span>
                        </button>
                    </div>
                </div>
            {:else}
                <!-- Properties List -->
                <div class="space-y-4">
                    {#each suggestions as property, index}
                        <div class="bg-white rounded-lg border border-[var(--border-light)] p-4">
                            <!-- Header -->
                            <div class="flex items-start justify-between mb-3">
                                <div>
                                    <h3 class="text-base font-semibold text-[var(--text-primary)] mb-1">
                                        {property.address}
                                    </h3>
                                    <div class="text-lg font-bold text-[var(--text-primary)]">
                                        {formatPrice(property.price)}
                                    </div>
                                </div>
                            </div>

                            <!-- Details -->
                            <div class="flex items-center gap-4 mb-3 text-sm text-[var(--text-secondary)]">
                                <span>{property.beds} bed</span>
                                <span>•</span>
                                <span>{property.baths} bath</span>
                                <span>•</span>
                                <span>{formatNumber(property.sqft)} sqft</span>
                                <span>•</span>
                                <span>{property.daysOnMarket} days</span>
                            </div>

                            <!-- Link -->
                            <a
                                href={property.sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                class="inline-flex items-center gap-1.5 text-sm font-medium text-[var(--text-primary)]"
                            >
                                <span>View details</span>
                                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                                </svg>
                            </a>
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>
