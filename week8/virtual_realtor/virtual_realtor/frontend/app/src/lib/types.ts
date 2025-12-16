// TypeScript types for User Preferences and Property Suggestions

export interface PriceRange {
  min?: number | null;
  max?: number | null;
}

export interface BedroomRange {
  min?: number | null;
  max?: number | null;
}

export interface BathroomRange {
  min?: number | null;
  max?: number | null;
}

export interface SqftRange {
  min?: number | null;
  max?: number | null;
}

export interface UserPreferences {
  userId: string;
  email?: string | null;
  priceRange?: PriceRange | null;
  zipCodes?: string[];
  bedrooms?: BedroomRange | null;
  bathrooms?: BathroomRange | null;
  sqft?: SqftRange | null;
  propertyType?: string | null;
  updatedAt?: string;
}

export interface PropertySuggestion {
  id?: string | null;
  address: string;
  price: number;
  beds: number;
  baths: number;
  sqft: number;
  daysOnMarket: number;
  source: string;
  sourceUrl: string;
}

export interface PropertySuggestionsResponse {
  suggestions: PropertySuggestion[];
  count: number;
  hasPreferences: boolean;
  message?: string;
  error?: string;
}

export interface PreferencesResponse {
  success?: boolean;
  userId?: string;
  updatedAt?: string;
  error?: string;
  hasPreferences?: boolean;
}

