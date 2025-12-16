// API client helpers for preferences and property suggestions

import { fetchAuthSession } from "aws-amplify/auth";
import type {
    UserPreferences,
    PropertySuggestionsResponse,
    PreferencesResponse,
} from "./types";

const API_BASE = ""; // Relative path (proxied)

/**
 * Get authentication header with Cognito ID token
 */
async function getAuthHeader(): Promise<HeadersInit> {
    try {
        console.log("=== getAuthHeader called ===");
        console.log("Getting auth session...");
        const session = await fetchAuthSession();
        console.log("Session obtained:", {
            hasTokens: !!session.tokens,
            hasIdToken: !!session.tokens?.idToken,
        });
        
        const token = session.tokens?.idToken?.toString();
        
        if (token) {
            console.log("✓ Auth token obtained (length:", token.length, ")");
            console.log("Token preview:", token.substring(0, 20) + "...");
            // Use Bearer prefix so proxies / gateways keep the header
            return { Authorization: `Bearer ${token}` };
        } else {
            console.error("❌ No auth token available!");
            console.error("Session details:", JSON.stringify(session, null, 2));
            return {};
        }
    } catch (error) {
        console.error("❌ Exception getting auth header:", error);
        return {};
    }
}

/**
 * Get user preferences
 */
export async function getUserPreferences(): Promise<UserPreferences | null> {
    try {
        console.log("Fetching user preferences...");
        const headers = await getAuthHeader();
        const response = await fetch(`${API_BASE}/api/user/preferences`, {
            headers,
        });

        console.log("Preferences response status:", response.status);

        if (response.status === 404) {
            console.log("No preferences found (404)");
            return null;
        }

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Preferences fetch failed:", response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Preferences loaded:", data);
        return data;
    } catch (error) {
        console.error("Error fetching user preferences:", error);
        throw error;
    }
}

/**
 * Save or update user preferences
 */
export async function saveUserPreferences(
    preferences: Partial<UserPreferences>
): Promise<PreferencesResponse> {
    try {
        console.log("Saving user preferences:", preferences);
        const headers = {
            "Content-Type": "application/json",
            ...(await getAuthHeader()),
        };

        const response = await fetch(`${API_BASE}/api/user/preferences`, {
            method: "PUT",
            headers,
            body: JSON.stringify(preferences),
        });

        const data = await response.json();
        console.log("Save preferences response:", response.status, data);

        if (!response.ok) {
            // Extract error details from validation error
            let errorMsg = "Failed to save preferences";
            if (data.detail) {
                if (Array.isArray(data.detail)) {
                    // Pydantic validation errors
                    errorMsg = data.detail.map((err: any) => 
                        `${err.loc.join('.')}: ${err.msg}`
                    ).join(', ');
                } else if (typeof data.detail === 'string') {
                    errorMsg = data.detail;
                }
            } else if (data.error) {
                errorMsg = data.error;
            } else if (data.details) {
                // Custom validation errors from backend
                errorMsg = Array.isArray(data.details) ? data.details.join(', ') : data.details;
            }
            
            console.error("Save preferences failed:", errorMsg);
            throw new Error(errorMsg);
        }

        return data;
    } catch (error: any) {
        console.error("Error saving user preferences:", error);
        throw error;
    }
}

/**
 * Get property suggestions based on user preferences
 */
export async function getPropertySuggestions(
    limit: number = 5
): Promise<PropertySuggestionsResponse> {
    try {
        console.log(`Fetching property suggestions (limit: ${limit})...`);
        const headers = await getAuthHeader();
        const url = `${API_BASE}/api/property-suggestions?limit=${limit}`;
        console.log("Request URL:", url);
        
        const response = await fetch(url, { headers });

        console.log("Suggestions response status:", response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error("Suggestions fetch failed:", response.status, errorText);
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("Suggestions response data:", data);
        return data;
    } catch (error) {
        console.error("Error fetching property suggestions:", error);
        throw error;
    }
}
