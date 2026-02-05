import type { SavedProperty, SavedPropertiesResponse, FavoritesCountResponse } from '$lib/types/favorites';
import type { PropertyData } from '$lib/types/favorites';

const API_BASE = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        let errorMessage = 'An error occurred';
        try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorData.error || errorData.message || errorMessage;
        } catch (e) {
            // Default error message
        }
        throw new Error(errorMessage);
    }
    return response.json();
}

export async function getSavedProperties(visitOnly: boolean, authHeaders: HeadersInit): Promise<SavedProperty[]> {
    const response = await fetch(`${API_BASE}/saved-properties?visit_only=${visitOnly}`, {
        headers: authHeaders
    });
    return handleResponse<SavedProperty[]>(response);
}

export async function getSavedCount(authHeaders: HeadersInit): Promise<FavoritesCountResponse> {
    const response = await fetch(`${API_BASE}/saved-properties/count`, {
        headers: authHeaders
    });
    return handleResponse<FavoritesCountResponse>(response);
}

export async function saveProperty(propertyId: string, propertyData: PropertyData, isVisit: boolean, authHeaders: HeadersInit): Promise<SavedProperty> {
    const response = await fetch(`${API_BASE}/saved-properties`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders
        },
        body: JSON.stringify({
            property_id: propertyId,
            property_data: propertyData,
            is_visit: isVisit
        })
    });
    return handleResponse<SavedProperty>(response);
}

export async function deleteProperty(propertyId: string, authHeaders: HeadersInit): Promise<void> {
    const response = await fetch(`${API_BASE}/saved-properties/${propertyId}`, {
        method: 'DELETE',
        headers: authHeaders
    });
    await handleResponse<{ message: string }>(response);
}

export async function toggleVisitFlag(propertyId: string, isVisit: boolean, authHeaders: HeadersInit): Promise<SavedProperty> {
    const response = await fetch(`${API_BASE}/saved-properties/${propertyId}/visit`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders
        },
        body: JSON.stringify({
            is_visit: isVisit
        })
    });
    return handleResponse<SavedProperty>(response);
}

export async function mergeSession(sessionId: string, authHeaders: HeadersInit): Promise<{ merged_count: number }> {
    const response = await fetch(`${API_BASE}/merge-session`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders
        },
        body: JSON.stringify({ sessionId })
    });
    return handleResponse<{ merged_count: number }>(response);
}
