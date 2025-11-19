<script lang="ts">
	import { onMount } from 'svelte';
	import { sendMessage, getChatHistory, clearChat } from '$lib/api';
	import type { Message } from '$lib/types';
	import { marked } from 'marked';
	import { Home, Send, Trash2 } from 'lucide-svelte';

	let messages: Message[] = [];
	let inputMessage = '';
	let isLoading = false;
	let isTyping = false;
	let messagesContainer: HTMLDivElement;
	let error: string | null = null;

	// Configure marked.js for markdown rendering
	marked.setOptions({
		breaks: true,
		gfm: true
	});

	onMount(() => {
		loadChatHistory();
	});

	async function loadChatHistory() {
		try {
			const data = await getChatHistory();
			messages = data.messages.map((msg) => ({
				role: msg.role as 'user' | 'assistant',
				content: msg.content[0].text
			}));
			scrollToBottom();
		} catch (e: any) {
			console.error('Error loading chat history:', e);
			error = 'Failed to load chat history. Please refresh the page.';
		}
	}

	async function handleSend() {
		if (!inputMessage.trim() || isLoading) return;

		const userMessage = inputMessage.trim();
		inputMessage = '';
		isLoading = true;
		isTyping = true;
		error = null;

		// Add user message
		messages = [...messages, { role: 'user', content: userMessage }];
		scrollToBottom();

		try {
			const response = await sendMessage(userMessage);
			const reader = response.body?.getReader();
			const decoder = new TextDecoder();
			let assistantMessage = '';

			if (!reader) throw new Error('No response stream');

			isTyping = false;

			// Add empty assistant message that we'll update
			const assistantMessageIndex = messages.length;
			messages = [...messages, { role: 'assistant', content: '' }];

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				const chunk = decoder.decode(value, { stream: true });
				const lines = chunk.split('\n');

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const data = line.slice(6).trim();
						if (data === '[DONE]' || data === '') continue;

						try {
							// Parse the JSON-encoded string to get the actual text
							const textChunk = JSON.parse(data);
							assistantMessage += textChunk;

							// Update the assistant message
							messages[assistantMessageIndex] = {
								role: 'assistant',
								content: assistantMessage
							};
							messages = [...messages]; // Trigger reactivity
							scrollToBottom();
						} catch (e) {
							// If JSON parsing fails, treat as plain text (fallback)
							console.warn('Failed to parse JSON chunk:', data);
							assistantMessage += data;

							messages[assistantMessageIndex] = {
								role: 'assistant',
								content: assistantMessage
							};
							messages = [...messages]; // Trigger reactivity
							scrollToBottom();
						}
					}
				}
			}
		} catch (e: any) {
			console.error('Error sending message:', e);
			error = 'Failed to send message. Please try again.';
			isTyping = false;
		} finally {
			isLoading = false;
		}
	}

	async function handleClearChat() {
		if (!confirm('Are you sure you want to clear the chat history?')) {
			return;
		}

		try {
			await clearChat();
			messages = [];
			error = null;
		} catch (e: any) {
			console.error('Error clearing chat:', e);
			error = 'Failed to clear chat. Please try again.';
		}
	}

	function handleKeyPress(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			handleSend();
		}
	}

	function scrollToBottom() {
		setTimeout(() => {
			if (messagesContainer) {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
		}, 10);
	}

	function renderMarkdown(content: string): string {
		return marked.parse(content) as string;
	}
</script>

<svelte:head>
	<title>Virtual Realtor</title>
</svelte:head>

<div class="min-h-screen gradient-bg flex items-center justify-center p-4">
	<div class="w-full max-w-4xl h-[85vh] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden">
		<!-- Header -->
		<div class="gradient-header px-6 py-4 flex items-center justify-between border-b border-emerald-400/30">
			<div class="flex items-center gap-3">
				<div class="flex flex-col">
					<h1 class="text-xl font-bold text-slate-900">Property Search Assistant</h1>
					<p class="text-xs text-slate-700 opacity-80">Ask me anything about properties for sale</p>
				</div>
			</div>
			<button
				onclick={handleClearChat}
				class="btn-secondary text-xs"
				type="button"
			>
				<Trash2 class="h-3.5 w-3.5" />
				Clear Chat
			</button>
		</div>

		<!-- Messages Container -->
		<div
			bind:this={messagesContainer}
			class="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-br from-slate-50 to-slate-100"
		>
			{#if error}
				<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-xl">
					{error}
				</div>
			{/if}

			{#each messages as message (message)}
				<div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
					<div
						class="message-bubble {message.role === 'user' ? 'message-bubble-user rounded-br-sm' : 'message-bubble-assistant rounded-bl-sm'}"
					>
						{#if message.role === 'assistant'}
							<div class="prose prose-sm max-w-none prose-slate">
								{@html renderMarkdown(message.content)}
							</div>
						{:else}
							<p class="whitespace-pre-wrap">{message.content}</p>
						{/if}
					</div>
				</div>
			{/each}

			{#if isTyping}
				<div class="flex justify-start">
					<div class="message-bubble message-bubble-assistant rounded-bl-sm flex items-center gap-2">
						<div class="flex gap-1">
							<span class="w-2 h-2 bg-slate-700 rounded-full animate-typing"></span>
							<span class="w-2 h-2 bg-slate-700 rounded-full animate-typing"></span>
							<span class="w-2 h-2 bg-slate-700 rounded-full animate-typing"></span>
						</div>
						<span class="text-sm text-slate-700">Thinking...</span>
					</div>
				</div>
			{/if}
		</div>

		<!-- Input Area -->
		<div class="border-t border-slate-200 bg-white p-6">
			<div class="flex gap-3">
				<input
					type="text"
					bind:value={inputMessage}
					onkeypress={handleKeyPress}
					disabled={isLoading}
					placeholder="Ask about properties, prices, locations..."
					maxlength={500}
					class="flex-1 px-4 py-3 rounded-full border-2 border-slate-300 focus:border-pink-400 focus:outline-none focus:ring-2 focus:ring-pink-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
				/>
				<button
					onclick={handleSend}
					disabled={isLoading || !inputMessage.trim()}
					class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
					type="button"
				>
					<Send class="h-5 w-5" />
					Send
				</button>
			</div>
		</div>
	</div>
</div>

