export interface PropertyData {
    id: string;
    formattedAddress: string;
    price: number;
    bedrooms: number;
    bathrooms: number;
    squareFootage: number;
    propertyType: string;
    city?: string;
    zipCode?: string;
    daysOnMarket?: number;
    source?: string;
    sourceUrl?: string;
    listingDate?: string;
    imageUrl?: string;
}

export interface SavedProperty extends PropertyData {
    property_id: string; // The backend uses property_id
    is_visit_candidate: boolean;
    favorited_at: string;
    last_refreshed_at: string;
    snapshot_price: number;
    snapshot_timestamp?: string;
    // Helper to distinguish from regular properties if needed
    isSavedProperty?: boolean;
}


export interface SavedPropertiesResponse {
    items: SavedProperty[];
    message?: string;
}

export interface FavoritesCountResponse {
    total: number;
    favorites: number;
    visit: number;
}
