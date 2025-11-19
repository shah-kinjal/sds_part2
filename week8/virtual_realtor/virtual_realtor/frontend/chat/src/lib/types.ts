export interface Message {
	role: 'user' | 'assistant';
	content: string;
}

export interface ChatResponse {
	messages: {
		role: string;
		content: Array<{ text: string }>;
	}[];
}

