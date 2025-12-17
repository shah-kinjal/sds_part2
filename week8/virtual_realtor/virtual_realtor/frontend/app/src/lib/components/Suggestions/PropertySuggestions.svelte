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

<div class="h-full flex flex-col items-center bg-[var(--bg-container)] overflow-hidden">
    <div class="w-full max-w-5xl mx-auto flex flex-col h-full">
        {#if isLoading}
            <!-- Loading State -->
            <div class="flex-1 flex items-center justify-center py-16">
            <div class="text-center animate-fade-in">
                <div class="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
                    <svg class="w-8 h-8 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-[var(--text-primary)] mb-2">
                    Finding Perfect Properties
                </h3>
                <p class="text-sm text-[var(--text-secondary)]">
                    Searching listings that match your preferences...
                </p>
            </div>
        </div>
    {:else if suggestions.length === 0}
        <!-- Empty State -->
        <div class="flex-1 flex items-center justify-center py-16 px-6">
            <div class="text-center max-w-md animate-fade-in">
                <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-[var(--bg-hover)] flex items-center justify-center">
                    <svg class="w-10 h-10 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
                    </svg>
                </div>
                <h3 class="text-xl font-bold text-[var(--text-primary)] mb-3">
                    No Properties Found
                </h3>
                <p class="text-sm text-[var(--text-secondary)] mb-6">
                    We couldn't find any properties matching your criteria. Try adjusting your preferences or refresh to see new listings.
                </p>
                <button
                    onclick={onRefresh}
                    class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white font-semibold hover:shadow-lg transition-all"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    <span>Refresh Listings</span>
                </button>
            </div>
        </div>
        {:else}
            <!-- Header -->
            <div class="bg-white border-b border-[var(--border-light)] px-6 py-5">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-2xl font-bold text-[var(--text-primary)]">
                        Your Property Matches
                    </h2>
                    <p class="text-sm text-[var(--text-secondary)] mt-1">
                        {suggestions.length} {suggestions.length === 1 ? 'property' : 'properties'} match your preferences
                    </p>
                </div>
                <button
                    onclick={onRefresh}
                    disabled={isLoading}
                    class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[var(--bg-container)] text-[var(--text-primary)] font-medium hover:bg-[var(--bg-hover)] disabled:opacity-50 transition-all border border-[var(--border-light)]"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    <span>Refresh</span>
                </button>
            </div>
        </div>

        <!-- Properties Grid -->
        <div class="flex-1 overflow-y-auto p-6">
            <div class="grid gap-6 grid-cols-1 md:grid-cols-2">
                {#each suggestions as property, index}
                    <div class="card hover:shadow-lg transition-all animate-scale-in bg-white" style="animation-delay: {index * 0.05}s;">
                        <div class="p-6">
                            <!-- Header with Index -->
                            <div class="flex items-start justify-between mb-4">
                                <div class="flex items-center gap-3">
                                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center text-white font-bold shadow-md">
                                        {index + 1}
                                    </div>
                                    <div class="flex-1">
                                        <h3 class="text-lg font-bold text-[var(--text-primary)] leading-tight">
                                            {property.address}
                                        </h3>
                                    </div>
                                </div>
                            </div>

                            <!-- Price -->
                            <div class="mb-6">
                                <div class="text-3xl font-bold bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                                    {formatPrice(property.price)}
                                </div>
                            </div>

                            <!-- Details Grid -->
                            <div class="grid grid-cols-2 gap-4 mb-6">
                                <div class="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-container)]">
                                    <div class="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl shadow-sm">
                                        🛏️
                                    </div>
                                    <div>
                                        <div class="text-lg font-bold text-[var(--text-primary)]">{property.beds}</div>
                                        <div class="text-xs text-[var(--text-muted)]">Bedroom{property.beds !== 1 ? 's' : ''}</div>
                                    </div>
                                </div>

                                <div class="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-container)]">
                                    <div class="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl shadow-sm">
                                        🛁
                                    </div>
                                    <div>
                                        <div class="text-lg font-bold text-[var(--text-primary)]">{property.baths}</div>
                                        <div class="text-xs text-[var(--text-muted)]">Bathroom{property.baths !== 1 ? 's' : ''}</div>
                                    </div>
                                </div>

                                <div class="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-container)]">
                                    <div class="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl shadow-sm">
                                        📏
                                    </div>
                                    <div>
                                        <div class="text-lg font-bold text-[var(--text-primary)]">{formatNumber(property.sqft)}</div>
                                        <div class="text-xs text-[var(--text-muted)]">Square Feet</div>
                                    </div>
                                </div>

                                <div class="flex items-center gap-3 p-3 rounded-lg bg-[var(--bg-container)]">
                                    <div class="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-xl shadow-sm">
                                        📅
                                    </div>
                                    <div>
                                        <div class="text-lg font-bold text-[var(--text-primary)]">{property.daysOnMarket}</div>
                                        <div class="text-xs text-[var(--text-muted)]">Days Listed</div>
                                    </div>
                                </div>
                            </div>

                            <!-- CTA Button -->
                            <a
                                href={property.sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                class="flex items-center justify-center w-full px-6 py-3 rounded-xl bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] text-white font-semibold hover:shadow-lg transition-all"
                            >
                                <span>Full Details</span>
                            </a>
                        </div>
                    </div>
                {/each}
                </div>
            </div>
        {/if}
    </div>
</div>
