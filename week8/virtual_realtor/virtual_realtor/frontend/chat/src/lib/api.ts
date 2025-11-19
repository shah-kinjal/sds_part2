import type { ChatResponse } from './types';

const API_BASE = '/api';

/**
 * Sends a message to the chat API and returns a streaming response
 */
export async function sendMessage(prompt: string): Promise<Response> {
	const response = await fetch(`${API_BASE}/chat`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ prompt }),
		credentials: 'include' // Include cookies for session management
	});

	if (!response.ok) {
		throw new Error(`Failed to send message: ${response.statusText}`);
	}

	return response;
}

/**
 * Gets the chat history
 */
export async function getChatHistory(): Promise<ChatResponse> {
	const response = await fetch(`${API_BASE}/chat`, {
		method: 'GET',
		credentials: 'include'
	});

	if (!response.ok) {
		throw new Error(`Failed to load chat history: ${response.statusText}`);
	}

	return response.json();
}

/**
 * Clears the chat history
 */
export async function clearChat(): Promise<void> {
	const response = await fetch(`${API_BASE}/chat`, {
		method: 'DELETE',
		credentials: 'include'
	});

	if (!response.ok) {
		throw new Error(`Failed to clear chat: ${response.statusText}`);
	}
}

