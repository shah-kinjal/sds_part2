<script module>
    import { Building } from "lucide-svelte";
</script>

<script lang="ts">
    import {
        Heart,
        Calendar,
        Trash2,
        ExternalLink,
        MapPin,
        Bed,
        Bath,
        Hash,
    } from "lucide-svelte";
    import type { PropertyData } from "$lib/types/favorites";

    interface Props {
        property: PropertyData;
        isSaved?: boolean;
        isInVisitList?: boolean;
        showActions?: boolean;
        onSave?: (id: string) => void;
        onAddToVisit?: (id: string) => void;
        onRemove?: (id: string) => void;
    }

    let {
        property,
        isSaved = false,
        isInVisitList = false,
        showActions = true,
        onSave,
        onAddToVisit,
        onRemove,
    }: Props = $props();

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

<div
    class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow duration-200 flex flex-col h-full group"
>
    <!-- Image / Placeholder -->
    <div class="relative h-48 bg-gray-200 overflow-hidden">
        {#if property.imageUrl}
            <img
                src={property.imageUrl}
                alt={property.formattedAddress}
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
        {:else}
            <div
                class="flex items-center justify-center h-full bg-gradient-to-br from-indigo-50 to-blue-50 text-indigo-200"
            >
                <Building class="w-16 h-16" />
            </div>
        {/if}

        <!-- Status Badges -->
        <div class="absolute top-2 left-2 flex gap-2">
            {#if property.propertyType}
                <span
                    class="px-2 py-1 text-xs font-semibold bg-white/90 backdrop-blur text-gray-700 rounded-md shadow-sm"
                >
                    {property.propertyType}
                </span>
            {/if}
            {#if property.daysOnMarket !== undefined}
                <span
                    class="px-2 py-1 text-xs font-semibold bg-blue-500/90 backdrop-blur text-white rounded-md shadow-sm"
                >
                    {property.daysOnMarket} days
                </span>
            {/if}
        </div>

        <!-- Visit List Badge -->
        {#if isInVisitList}
            <div
                class="absolute top-2 right-2 px-2 py-1 text-xs font-bold bg-green-500 text-white rounded-md shadow-sm flex items-center gap-1"
            >
                <Calendar class="w-3 h-3" />
                Visit List
            </div>
        {/if}
    </div>

    <!-- Content -->
    <div class="p-4 flex flex-col flex-1">
        <div class="flex justify-between items-start mb-2">
            <div>
                <h3 class="text-xl font-bold text-gray-900">
                    {formatPrice(property.price)}
                </h3>
                <p class="text-sm text-gray-600 flex items-start gap-1 mt-1">
                    <MapPin class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span class="line-clamp-2">{property.formattedAddress}</span
                    >
                </p>
            </div>
        </div>

        <!-- Features -->
        <div
            class="grid grid-cols-3 gap-2 py-3 border-t border-b border-gray-100 my-3"
        >
            <div class="flex flex-col items-center">
                <span
                    class="flex items-center gap-1 text-sm font-semibold text-gray-900"
                >
                    <Bed class="w-4 h-4 text-gray-400" />
                    {property.bedrooms}
                </span>
                <span class="text-xs text-gray-500">Beds</span>
            </div>
            <div class="flex flex-col items-center border-l border-gray-100">
                <span
                    class="flex items-center gap-1 text-sm font-semibold text-gray-900"
                >
                    <Bath class="w-4 h-4 text-gray-400" />
                    {property.bathrooms}
                </span>
                <span class="text-xs text-gray-500">Baths</span>
            </div>
            <div class="flex flex-col items-center border-l border-gray-100">
                <span
                    class="flex items-center gap-1 text-sm font-semibold text-gray-900"
                >
                    <Hash class="w-4 h-4 text-gray-400" />
                    {property.squareFootage
                        ? formatNumber(property.squareFootage)
                        : "-"}
                </span>
                <span class="text-xs text-gray-500">Sq Ft</span>
            </div>
        </div>

        <div class="mt-auto flex items-center justify-between pt-2">
            {#if property.sourceUrl}
                <a
                    href={property.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                >
                    View listing <ExternalLink class="w-3 h-3" />
                </a>
            {:else}
                <div></div>
            {/if}

            {#if showActions}
                <div class="flex items-center gap-2">
                    <!-- Save Button -->
                    {#if onSave}
                        <button
                            class="p-2 rounded-full transition-colors duration-200 {isSaved
                                ? 'bg-red-50 text-red-500 hover:bg-red-100'
                                : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'}"
                            onclick={() => onSave(property.id)}
                            title={isSaved
                                ? "Remove from favorites"
                                : "Save to favorites"}
                            aria-label={isSaved
                                ? "Remove from favorites"
                                : "Save to favorites"}
                        >
                            <Heart
                                class="w-5 h-5 {isSaved ? 'fill-current' : ''}"
                            />
                        </button>
                    {/if}

                    <!-- Visit List Button -->
                    {#if onAddToVisit}
                        <button
                            class="p-2 rounded-full transition-colors duration-200 {isInVisitList
                                ? 'bg-green-50 text-green-600 hover:bg-green-100'
                                : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'}"
                            onclick={() => onAddToVisit(property.id)}
                            title={isInVisitList
                                ? "In visit list"
                                : "Add to visit list"}
                            aria-label={isInVisitList
                                ? "In visit list"
                                : "Add to visit list"}
                        >
                            <Calendar
                                class="w-5 h-5 {isInVisitList
                                    ? 'fill-current'
                                    : ''}"
                            />
                        </button>
                    {/if}

                    <!-- Remove Button (e.g. from visit list view) -->
                    {#if onRemove}
                        <button
                            class="p-2 rounded-full bg-gray-100 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors duration-200"
                            onclick={() => onRemove(property.id)}
                            title="Remove"
                            aria-label="Remove"
                        >
                            <Trash2 class="w-5 h-5" />
                        </button>
                    {/if}
                </div>
            {/if}
        </div>
    </div>
</div>
